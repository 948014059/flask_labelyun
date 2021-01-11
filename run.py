from flask import Flask,jsonify,request,send_file,make_response,render_template
from flask_cors import CORS
import time
import os
import zipfile
from gevent import pywsgi

app=Flask(__name__)

app = Flask(__name__,
            static_folder = "./dist/static",
            template_folder = "./dist")

cors = CORS(app, resources={"/*": {"origins": "*"}})

# 映射到vue的index.html
@app.route('/',defaults={'path':''})
@app.route('/<path:path>')
def index(path):
    return render_template("index.html")

g_path=os.getcwd()

def write_txt(name,list):
    with open(name,'w',encoding='utf8') as f:
        f.writelines(list)

# 压缩文件
def zip_file(absDir,zipFile):
    for f in os.listdir(absDir):
        absFile = os.path.join(absDir, f)  # 子文件的绝对路径
        relFile = absFile[len(os.getcwd()) + 1:]  # 改成相对路径
        # print(relFile)
        zipFile.write(relFile)
    # return


@app.route('/api/labelyun',methods=['POST'])
def post_labelyun():
    global g_path
    if request.method == 'POST':
        data_lists=request.get_json()['data']
        label_lists=request.get_json()['label']

        print(request.get_json())
        if len(data_lists)!=0 and len(label_lists)!=0:
            make_time=str(time.time()).split('.')[0]
            make_files_path=g_path+'/data_zip_files/%s'%make_time
            os.makedirs(make_files_path)

            label_=[]
            for label in label_lists:
                label_.append(label['name']+'\n')

            write_txt(make_files_path+'/label.txt',label_)

            # print(label_)
            label_without_n=[x.strip() for x in label_ if x.strip()!='']

            name_label=[]
            for data in data_lists:
                res=''
                name=data['name']
                h,w=data['hw'].split('x')
                chooes_boxs=data['data']
                res+=name+' '
                for box in chooes_boxs:
                    tag=box['tagName']
                    try:
                        x= int(float(box['position']['x'][:5])*int(w)*0.01)
                        y=int(float(box['position']['y'][:5])*int(h)*0.01)
                        x1=int(float(box['position']['x1'][:5])*int(w)*0.01)
                        y1=int(float(box['position']['y1'][:5])*int(h)*0.01)
                    except:
                        x = int(float(box['position']['x'][:2]) * int(w) * 0.01)
                        y = int(float(box['position']['y'][:2]) * int(h) * 0.01)
                        x1 = int(float(box['position']['x1'][:2]) * int(w) * 0.01)
                        y1 = int(float(box['position']['y1'][:2]) * int(h) * 0.01)
                    res+='%s,%s,%s,%s,%s '%(x,y,x1,y1,label_without_n.index(tag))
                name_label.append(res+'\n')
                write_txt(make_files_path+r'/train.txt',name_label)

            zip_files=zipfile.ZipFile('%s/%s.zip'%(g_path+'/data_zip_files',make_time),'w')
            zip_file(make_files_path, zip_files)
            zip_files.close()
            return jsonify({'flag':'success','zip_name':make_time})
        else:
            return jsonify({'flag':'error','msg':'null'})

@app.route('/api/download_zip',methods=['GET'])
def download_zip():
    global g_path
    name=request.args.get('name')
    response = make_response(send_file('%s/data_zip_files/%s.zip' % (g_path,name)))
    response.headers["Content-Disposition"] = "p_w_upload; filename=%s.zip;"%name
    return response

if __name__ == '__main__':
    server = pywsgi.WSGIServer(('192.168.3.*',6001),app)
    server.serve_forever()
    # app.run(host='192.168.3.203',port=6001,debug=False)
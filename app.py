import sys
from os import walk
import imghdr
import csv
import argparse
import logging

from flask import Flask, redirect, url_for, request
from flask import render_template
from flask import send_file
from flask_sqlalchemy import SQLAlchemy 


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
###database####
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Channel(db.Model):
    image_name = db.Column(db.String(255), primary_key=True)
    caption = db.Column(db.String(255))
    xMax = db.Column(db.Float)
    xMin = db.Column(db.Float)
    yMax = db.Column(db.Float)
    yMin = db.Column(db.Float)

    def __repr__(self):
        return f"Channel('{self.image_name}','{self.caption}','{self.xMax}','{self.xMin}','{self.yMax}','{self.yMin}')"

def addQuery(image_name,caption, xMax, xMin,yMax,yMin):
    query = Channel(image_name=image_name,caption=caption,xMax=xMax, xMin=xMin, yMax=yMax,yMin=yMin)
    db.session.add(query)
    db.session.commit()


@app.route('/tagger')
def tagger():
    if (app.config["HEAD"] == len(app.config["FILES"])):
        return redirect(url_for('bye'))
    directory = app.config['IMAGES']
    image = app.config["FILES"][app.config["HEAD"]]
    labels = app.config["LABELS"]
    not_end = not(app.config["HEAD"] == len(app.config["FILES"]) - 1)
    print(not_end)
    return render_template('tagger.html', not_end=not_end, directory=directory, image=image, labels=labels, head=app.config["HEAD"] + 1, len=len(app.config["FILES"]))

@app.route('/next')
def next():
    image = app.config["FILES"][app.config["HEAD"]]
    app.config["HEAD"] = app.config["HEAD"] + 1
    with open(app.config["OUT"],'a') as f:
        for label in app.config["LABELS"]:
            addQuery(image,label["name"],label["xMax"],label["xMin"],label["yMax"],label["yMin"])
            # print('label["name"]------>',label["name"])
            f.write(image + "," +
            label["id"] + "," +
            label["name"] + "," +
            str(round(float(label["xMin"]))) + "," +
            str(round(float(label["xMax"]))) + "," +
            str(round(float(label["yMin"]))) + "," +
            str(round(float(label["yMax"]))) + "\n")
    app.config["LABELS"] = []
    return redirect(url_for('tagger'))

@app.route("/bye")
def bye():
    return send_file("taf.gif", mimetype='image/gif')

@app.route('/add/<id>')
def add(id):
    xMin = request.args.get("xMin")
    xMax = request.args.get("xMax")
    yMin = request.args.get("yMin")
    yMax = request.args.get("yMax")
    name = request.args.get("name")
    app.config["LABELS"].append({"id":id, "name":"", "xMin":xMin, "xMax":xMax, "yMin":yMin, "yMax":yMax})
    return redirect(url_for('tagger'))

@app.route('/remove/<id>')
def remove(id):
    index = int(id) - 1
    del app.config["LABELS"][index]
    for label in app.config["LABELS"][index:]:
        label["id"] = str(int(label["id"]) - 1)
    return redirect(url_for('tagger'))

@app.route('/label/<id>')
def label(id):
    name = request.args.get("name")
    app.config["LABELS"][int(id) - 1]["name"] = name
    return redirect(url_for('tagger'))
# @app.route('/prev')
# def prev():
#     app.config["HEAD"] = app.config["HEAD"] - 1
#     return redirect(url_for('tagger'))

@app.route('/image/<f>')
def images(f):
    images = app.config['IMAGES']
    return send_file(images + f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', type=str, help='specify the images directory')
    parser.add_argument("--out")
    args = parser.parse_args()
    directory = args.dir
    if directory[len(directory) - 1] != "/":
         directory += "/"
    app.config["IMAGES"] = directory
    app.config["LABELS"] = []
    files = None
    for (dirpath, dirnames, filenames) in walk(app.config["IMAGES"]):
        files = filenames
        break
    if files == None:
        print("No files")
        exit()
    app.config["FILES"] = files
    app.config["HEAD"] = 0
    if args.out == None:
        app.config["OUT"] = "out.csv"
    else:
        app.config["OUT"] = args.out
    print(files)
    with open("out.csv",'w') as f:
        f.write("image,id,name,xMin,xMax,yMin,yMax\n")
    app.run(debug=True)
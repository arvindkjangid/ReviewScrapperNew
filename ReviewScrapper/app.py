from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo
import csv

app = Flask(__name__)

@app.route('/', methods = ['GET']) #routeto display the home page
@cross_origin()
def home():
    return render_template('index.html')

@app.route('/review', methods = ['POST','GET'])
@cross_origin()
def index():
    if request.method == 'POST':
        searchString = request.form['content'].replace(" ", "")

        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")
            db = dbConn['crawlerDB']
            reviews = db[searchString].find({})
            if reviews.count()>0:
                return render_template('results.html',reviews=reviews)
            else:
                flipkart_url = "https://www.flipkart.com/search?q=" + searchString
                uClient = uReq(flipkart_url)
                flipkartPage =uClient.read()
                uClient.close()
                flipkart_html = bs(flipkartPage,"html.parser")
                bigboxes = flipkart_html.find_all("div",{"class":"bhgxx2 col-12-12"})
                del bigboxes[0:3]
                box = bigboxes[0]
                productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
                prodRes = requests.get(productLink)
                prodRes.encoding = "utf-8"
                prod_html = bs(prodRes.text,"html.parser")
                commentboxes = prod_html.find_all("div",{"class":"_3nrCtb"})

                filename = searchString + ".csv"
                #fw = open(filename,"w+", newline='')
                #headers = "Product, Customer Name, Rating, Comment Head, Comment \n"
                #fw.write(['Product','Customer Name','Rating','Comment Head','Comment'])
                reviews = []
                for commentbox in commentboxes:
                    try:
                        name = commentbox.find_all("p",{"class":"_3LYOAd _3sxSiS"})[0].text
                    except:
                        name = "No Name"

                    try:
                        rating = commentbox.find_all("div",{"class":"hGSR34 E_uFuv"})[0].text
                    except:
                        rating = "No Rating"

                    try:
                        commentHead = commentbox.find_all("p",{"class","_2xg6Ul"})[0].text
                    except: "No Comment Head"

                    try:
                        custComment = commentbox.find_all("div",{"class":"qwjRop"})[0].text
                    except Exception as e:
                        print("Exception while creating dictionary: ", e)

                    mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead":commentHead,
                              "Comment": custComment}


                    """
                    for line in mydict:
                    csv_writer.writerow(line)
                    """
                    reviewDetails = db.reviewDetails
                    record = {
                        'Product':searchString,
                        'Name':name,
                        'Rating':rating,
                        'CommentHead':commentHead,
                        'Comment':custComment
                    }

                    reviewDetails.insert_one(record)


                    reviews.append(mydict)
                    """
                    reviewDetails = db.reviewDetails
                    reviewDetails.insert_many(reviews)
                    """

                    headers = ["Product","Name","Rating","CommentHead", "Comment"]
                    csv_writer = csv.DictWriter(open(filename, 'w'), fieldnames=headers, delimiter=',')
                    csv_writer.writeheader()
                    csv_writer.writerows(reviews)
                return render_template('results.html', reviews=reviews[0:(len(reviews)-1)])
        except Exception as e:
            print("The Exception message is:",e)
            return "something is wrong"

    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
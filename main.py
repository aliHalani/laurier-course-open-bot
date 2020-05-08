import requests
import psycopg2
import os

course_data = [{"term": "202005",
                "courseReferenceNumber": "1077",
                "title" : "Financial Markets & Securities Trading",
                "email": "testemail@mylaurier.ca"}
                ]

def sendMail(course, seats):
    return requests.post(
		"https://api.mailgun.net/v3/sandbox61f41eea06224b42b90bb64221d155c6.mailgun.org/messages",
		auth=("api", os.environ["MAILGUN_API_KEY"]),
		data={"from": "Laurier Course Bot <postmaster@sandbox61f41eea06224b42b90bb64221d155c6.mailgun.org>",
			"to": "<" + course["email"] + ">",
			"subject": "Open Spot - " + course["title"],
			"html": str(seats) + " spots open"})


def checkSeats(data):
    req = requests.post("https://loris.wlu.ca/register/ssb/searchResults/getEnrollmentInfo", 
                        headers={"accept":"text/html", 
                                 "content-type":"application/x-www-form-urlencoded; charset=UTF-8",
                                 "sec-fetch-mode":"cors",
                                 "sec-fetch-site":"same-origin",
                                 "x-requested-with":"XMLHttpRequest"},
                        data=data)

    spots = req.text[req.text.find("ment Seats Available:</span> <span dir=\"ltr\"> ") + 
                                        len("ment Seats Available:</span> <span dir=\"ltr\"> "):
                                        req.text.find(" </span>", req.text.find("ment Seats Available:</span> <span dir=\"ltr\"> ") + 
                                        len("ment Seats Available:</span> <span dir=\"ltr\"> "))]
    return int(spots)

if __name__ == "__main__":
    for course in course_data:
        open_seats = checkSeats(course)
        if open_seats != 0:
            conn = psycopg2.connect(os.getenv("DATABASE_URL"))
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute("SELECT * FROM PUBLIC.courses WHERE id=%s", (course["courseReferenceNumber"],))
            if cur.rowcount != 0:
                print(course["title"], "already notified")
            elif sendMail(course, open_seats).status_code == 200:
                cur.execute("INSERT INTO PUBLIC.courses(id) values(%s)", (course["courseReferenceNumber"],))
                print("Inserted", course["title"])
                cur.close()
                conn.close()
        else:
            print(course["title"], "is full")
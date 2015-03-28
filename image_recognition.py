import webbrowser
import threading
import cv2
import os
import csv

c = cv2.VideoCapture(1)
frame = []
kill = False #for killing all threads

files = os.listdir("produkty") #comparison images listing
images = []
links = []

for fileName in files:
    images.append(cv2.imread("produkty/"+fileName)) #loading product images

with open('links.txt', 'r') as csvFile: #loading products' links
        csvReader = csv.reader(csvFile, delimiter=";")
        for row in csvReader:
            insertrow = [row[0], row[1], 0]
            links.append(insertrow)
csvFile.close()

kp = []
des = []

sift = cv2.SIFT()
surf = cv2.SURF(500)
surf.extended = True
surf.upright = True
method = sift

def showPermit(i): #letting product website open again (after 5sec) 
    links[i][2] = 0

for img in images:
    kp0, des0 = method.detectAndCompute(img, None) #calculating product images descriptors
    kp.append(kp0)
    des.append(des0)

index_params = dict(algorithm=0, trees=5)
search_params = dict(checks=100)

last = -2 #index of previous successfully identified product (double verification)
limit = 24 #minimum number of matches for positive verification


def compare():
    if kill:
        return 0

    threading.Timer(0.4, compare).start() #recursive creation of frame analysis threads (every 0.4sec)

    matchhits = []
    matches = []
    hits = []
    max = 0
    winner = -1
    global last

    kpframe, desframe = method.detectAndCompute(frame, None) #frame descriptors calculation

    flann = cv2.FlannBasedMatcher(index_params, search_params)

    for d in des:
        matches.append(flann.knnMatch(d, desframe, k=2)) #descriptors comparison

    for match in matches: #selection of acceptable matches
        for m, n in match:
            if m.distance < 0.7*n.distance:
                matchhits.append(m)
        hits.append(len(matchhits))
        matchhits = []

    for i, hit in enumerate(hits): #matching and decision
        if hit > max and hit > limit:
            max = hit
            winner = i

    if winner > -1 and last == winner: #decision about opening the website (double verification)
        print files[winner][:-4]
        for i, product in enumerate(links):
            if files[winner][:-4] == product[0]:
                if product[2] == 0:
                    webbrowser.open(product[1])
                    product[2] = 1 #blocking from opening the website again...
                    threading.Timer(5.0, showPermit, [i]).start() #...for 5sec

    print hits

    if winner > -1:
        last = winner
    else:
        last = -2

threading.Timer(2.0, compare).start() #start of camera image analysis

while(1):
    _,f = c.read() #camera read
    frame = f
    cv2.imshow('SIFT',f) #camera preview

    if cv2.waitKey(5)==27: #[ESC] kill threads and close app
        kill = True
        break

    if cv2.waitKey(5)==43: #[+] increase verification limit
        limit+=1
        print limit
    if cv2.waitKey(5)==45: #[-] decrease verification limit
        limit-=1
        print limit

cv2.destroyAllWindows()
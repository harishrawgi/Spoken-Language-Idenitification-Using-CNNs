import os
directory = "C:/Users/shraw/Python Workspace/lid/Spoken-language-identification-master/data/spectograms/portugese" 
f = open('listfile.csv','a')
for filename in os.listdir(directory):
    if filename.endswith(".png"):
        listfile = filename[:-4] + ",4\n"
        print(listfile)
        f.write(listfile)

f.close()

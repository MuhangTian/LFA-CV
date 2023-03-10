''' Helpers with data cleaning, analysis '''
import os
import numpy as np
import pandas as pd
import xml.etree.ElementTree as et
import json
import seaborn as sns
import matplotlib.pyplot as plt

def cont_int(path, num):
    """ Check whether files in a directory has consecutive integer names starting from num """
    files = os.listdir(path)
    try: files.remove('.DS_Store')
    except: files
    files = sorted([int(e.replace('.jpg', '')) for e in files])
    for i in range(num, num+len(files)):
        if i == files.pop(0): continue
        else: return False
    return True

def get_inter(arr1, arr2):
    """ Obtain intersection of two arrays """
    arr2, arr1 = set(arr2), set(arr1)
    arr = []
    for e in arr1:
        if e in arr2: arr.append(e)
    return arr

def get_comp(A, B):
    '''Obtain A not in B'''
    B, A = set(B), set(A)
    arr = []
    for e in A:
        if e not in B: arr.append(e)
    return arr

def files_rename(path, start):
    """
    Rename all files in a directory according to consecutive integers

    Args:
        path (str): path of directory
        start (int): start of the numbering
    """
    files = os.listdir(path)
    try: files.remove('.DS_Store')
    except: files
    int_arr = ['{}.jpg'.format(i) for i in range(start, start+len(files))]
    inter_files = get_inter(int_arr, files)
    inter_int = [int(e.replace('.jpg', '')) for e in inter_files]
    comp_files = get_comp(files, inter_files)
    comp_int = get_comp(np.arange(start, start+len(files)).tolist(), inter_int)
    
    before = len(os.listdir(path)) - 1
    c = 0
    for file in comp_files: 
        os.rename('{}/{}'.format(path, file), '{}/{}.jpg'.format(path, comp_int[c]))
        c += 1
    after = len(os.listdir(path)) - 1
    
    if before == after: 
        print('No files lost :)')
        print('Number of images: {}'.format(before))
    else: print('Files lost!!! :(')
    print('File names are consecutive integers from {}: {}'.format(start, cont_int(path, start)))
    if before == after and cont_int(path,start) == True:
        ph = 'SUCCESS'
    else: ph = 'FAILED'
    print('---------------------- {} ----------------------'.format(ph))

def find_rotated(path, start=None, num=None):
    '''Output IDs of all images that have rotated bounding box'''
    f = open(path)
    j = json.load(f)
    id = []
    c = 0
    for e in j:
        try:
            rotation = e['annotations'][0]['result'][0]['value']['rotation']
            c += 1
            if rotation != 0: 
                id.append(e['id'])
        except: continue
    if len(id) == 0: print('All bounding boxese are NOT rotated')
    elif num == None and start == None: print('Total Images: {}\nRotated IDs: {}'.format(c, id))
    elif num == None: print('Total Images: {}\nRotated IDs: {}'.format(c, id[id.index(start):]))
    elif start == None: print('Total Images: {}\nRotated IDs: {}'.format(c, id[:num]))
    else: print('Total Images: {}\nRotated IDs: {}'.format(c, id[id.index(start):id.index(start)+num]))

def find_overlabel(path):
    ''' Output IDs of all images with more than one label '''
    files = os.listdir(path)
    try: files.remove('.DS_Store')
    except: files
    arr = []
    for file in files:
        xtree = et.parse('{}/{}'.format(path, file))
        root = xtree.getroot()
        c = 0
        for child in root.findall('object'): c += 1
        if c > 1: arr.append(root.findall('filename')[0].text)
    print('Overlabelled: {}'.format(arr))

def drop_dash(path):
    ''' drop all letters before - in the directory of image files '''
    files1 = os.listdir('{}/Annotations'.format(path))
    files2 = os.listdir('{}/images'.format(path))
    try: 
        files1.remove('.DS_Store')
        files2.remove('.DS_Store')
    except: pass
    for file in files1:
        arr = file.split('-')
        os.rename('{}/Annotations/{}'.format(path, file), '{}/Annotations/{}'.format(path, arr[1]))
    for file in files2:
        arr = file.split('-')
        os.rename('{}/images/{}'.format(path, file), '{}/images/{}'.format(path, arr[1]))
        
def xml_csv(path, out_path, out_name):
    """
    Parse .xml annotation files from Pascal VOC format into .csv

    Args:
        path (str): path of the annotation folder with .xml files
        out_path (str): path where .csv file is created
        out_name (str): out_name.csv stored in out_path
    """
    files = os.listdir(path)
    try: files.remove('.DS_Store')
    except: files
    dict = {}
    for file in files:
        xtree = et.parse('{}/{}'.format(path, file))
        root = xtree.getroot()
        try: dict[root.findall('filename')[0].tag].append(root.findall('filename')[0].text)
        except: dict[root.findall('filename')[0].tag] = [root.findall('filename')[0].text]
        for child in root.findall('size'):
            for child2 in child:
                try: dict[child2.tag].append(child2.text)
                except: dict[child2.tag] = [child2.text]
        for child in root.findall('object'):
            for child2 in child:
                if child2.tag == 'name':
                    try: dict['label'].append(child2.text)
                    except: dict['label'] = [child2.text]
                elif child2.tag == 'bndbox':
                    for child3 in child2:
                        try: dict[child3.tag].append(child3.text)
                        except: dict[child3.tag] = [child3.text]
    df = pd.DataFrame(dict)
    df.replace('(.*)-', '', inplace=True, regex=True)
    df['label'].replace({'Negative': 1, 'Positive': 2}, inplace=True)
    df = df.reindex(columns=['label', 'filename', 'width', 'height', 'depth', 'xmin', 'ymin', 'xmax', 'ymax'])
    df_train = df.sample(frac=0.8)
    df_val = df.drop(df_train.index)
    df_train.to_csv(f"{out_path}/{out_name}_train.csv", index=False)
    df_val.to_csv(f"{out_path}/{out_name}_test.csv", index=False)
    df.to_csv(f"{out_path}/{out_name}.csv", index=False)
    print(f"============== csvs created in <{out_path}> ==============")

class EDA():
    """
    Class for Exploratory Data Analysis of the dataset
    """
    def __init__(self, csv_path) -> None:
        self.df = pd.read_csv(csv_path)
        self.df['area'] = self.df['width']*self.df['height']
        self.df['volume'] = self.df['width']*self.df['height']*self.df['depth']
        self.df['box area'] = (self.df['xmax'] - self.df['xmin']) * (self.df['ymax'] - self.df['ymin'])
    
    def image_dist(self):
        color = iter(['b', 'r', 'y', 'purple', 'pink', 'brown', 'c'])
        for e in ['width', 'height', 'depth', 'area', 'volume']:
            sns.histplot(self.df[e], color=next(color))
            plt.title('{} Distribution, mean: {}, std: {}'.format(e, np.mean(self.df[e]), np.std(self.df[e])))
            plt.show()

    def coord_dist(self):
        color = iter(['b', 'r', 'y', 'purple', 'pink', 'brown', 'c'])
        for e in ['xmax', 'xmin', 'ymax', 'ymin', 'box area']:
            sns.histplot(self.df[e], color=next(color))
            plt.title('{} Distribution, mean: {}, std: {}'.format(e, np.mean(self.df[e]), np.std(self.df[e])))
            plt.show()

    def label(self):
        prop = 100*len(self.df[self.df['label'] == 2])/len(self.df['label'])
        print('Positive: {} Negative: {}\nPercent of positives: {}'.format(len(self.df[self.df['label'] == 2]),
                                                                           len(self.df[self.df['label'] == 1]),
                                                                           prop))


if __name__ == '__main__':
    # xml_csv('data/self-data/Annotations', 'data', 'self-data')
    # print(pd.read_csv('data/self-data_train.csv').shape[0])
    eda = EDA('data/self-data.csv')
    print(eda.label())
    
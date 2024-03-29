# -*- coding: utf-8 -*-
"""TweetSentimentFinal.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1my3Vliv4qJ_cEMrOrIkNAE0cOf4Yy4th

# **Import Libraries**
"""

import pandas as pd
#open source data analysis and manipulation tool
import nltk
# Natural Language Toolkit
import seaborn as sns 
#Library for diagrams
import numpy as np
#library for arrays
from textblob import TextBlob
#Library for processing textual data
import re as regex
import re
nltk.download('punkt')  
# Natural Language Toolkit
from collections import Counter
# sklearn library for train-test,accuracy-recall-precision score and time
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, RandomizedSearchCV
# time library for calculate time
from time import time
#precision, recall and and accuracy score from sklearn.metrics libraty  
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score

"""# **Input Files (Data)**"""

#Read .csv files into train and test data with the right encoding!
train_data = pd.read_csv('/content/SocialMedia.csv', encoding= 'unicode_escape')
test_data = pd.read_csv('/content/SocialMedia2.csv', encoding= 'unicode_escape')





train_data = train_data[train_data['Sentiment'] != 'Text']

# Analyze the 1st 5 posts of train_data file
train_data.head()

# Info for the train_data file
train_data.info()

# Analyze the 1st 5 posts of test_data file
test_data.head()

# Info for the test_data file
test_data.info()

"""# **Data Visualization**"""

# Diagram of the train_data file with number of posts and negantive files
sns.countplot(x='Sentiment',data=train_data)

sns.countplot(x='Sentiment',data=test_data)

"""# **Data Training**

# **Remove Empty Tweets**
"""

# remove tweets with empty sentiment column

train_data = train_data[train_data['Sentiment'] != ""]

train_data.info()

"""# **Tweet Cleaning**"""

#Function to clean tweets
 #Remove URLs
 #Remove usernames (mentions)
 #Remove special characters EXCEPT FROM :,)
 #Remove Numbers 



def clean_tweets(tweet):
    
    # remove URL
    tweet = re.sub(r"http\S+", "", tweet)
    
    # Remove usernames
    tweet = re.sub(r"@[^\s]+[\s]?",'',tweet)

     # remove special characters 
    tweet = re.sub('[^ a-zA-Z0-9]' , '', tweet)
    
    # remove Numbers
    tweet = re.sub('[0-9]', '', tweet)
    
    
    
    
    
    return tweet

# Apply function to Text column with clean text
train_data['Text'] = train_data['Text'].apply(clean_tweets)

#Analyze the 1st 5 posts of train_data file after cleaning with Name of column and datatype!
train_data['Text'].head()

"""# **Tokenize & Stremming**"""

# Function which directly tokenize the text data
from nltk.tokenize import TweetTokenizer

tt = TweetTokenizer()
train_data['Text'].apply(tt.tokenize)

from nltk.stem import PorterStemmer   #Libraries for tokenize words and stremming
from nltk.tokenize import sent_tokenize, word_tokenize

ps = PorterStemmer()

def tokenize(text):                    # funtion for tokenize words and stremming
    return word_tokenize(text)

def stemming(words):
    stem_words = []
    for w in words:
        w = ps.stem(w)
        stem_words.append(w)
    
    return stem_words

# apply tokenize function
train_data['tokenized'] = train_data['Text'].apply(tokenize)

# apply stemming function
train_data['stremming'] = train_data['tokenized'].apply(stemming)

train_data.head()  #See the 1st 5 tokenize reults

"""# **Wordlist file**"""

words = Counter()                       # Words analyze  (5 most common) with count of them
for idx in train_data.index:
    words.update(train_data.loc[idx, "tokenized"])

words.most_common(5)

nltk.download('stopwords')
stopwords=nltk.corpus.stopwords.words("english")

whitelist = ["n't", "not"]
for idx, stop_word in enumerate(stopwords):
    if stop_word not in whitelist:
        del words[stop_word]
words.most_common(5)

def word_list(processed_data): # wORDLIST FUNCTION FOR ANALYZE MOST COMMON WORDS WITH PURPOSE TO IDENTIFY OUR APP THE REAL SENTIMENT
    #print(processed_data)
    min_occurrences=3 
    max_occurences=500 
    stopwords=nltk.corpus.stopwords.words("english")
    whitelist = ["n't","not"]
    wordlist = []
    
    whitelist = whitelist if whitelist is None else whitelist
    
    words = Counter()
    for idx in processed_data.index:
        words.update(processed_data.loc[idx, "tokenized"])

    for idx, stop_word in enumerate(stopwords):
        if stop_word not in whitelist:
            del words[stop_word]
    #print(words)

    word_df = pd.DataFrame(data={"word": [k for k, v in words.most_common() if min_occurrences < v < max_occurences],
                                 "occurrences": [v for k, v in words.most_common() if min_occurrences < v < max_occurences]},
                           columns=["word", "occurrences"])
    #print(word_df)
    word_df.to_csv("wordlist.csv", index_label="idx")
    wordlist = [k for k, v in words.most_common() if min_occurrences < v < max_occurences]
    #print(wordlist)

word_list(train_data)    #TRAIN DATA INTO WORDLIST FOR ANALYZE

words = pd.read_csv("wordlist.csv") #CREATE WORDLIST CSV WITH THE MOST COMMON WORDS

"""# **Bag of Words**"""

import os
wordlist= []      #CREATE THE FILE WORDLIST
if os.path.isfile("wordlist.csv"):
    word_df = pd.read_csv("wordlist.csv")
    word_df = word_df[word_df["occurrences"] > 3]
    wordlist = list(word_df.loc[:, "word"])

label_column = ["label"]
columns = label_column + list(map(lambda w: w + "_bow",wordlist))
labels = []
rows = []
for idx in train_data.index:
    current_row = []
    
    # add label
    current_label = train_data.loc[idx, "Sentiment"]
    labels.append(current_label)
    current_row.append(current_label)

    # add bag-of-words
    tokens = set(train_data.loc[idx, "tokenized"])
    for _, word in enumerate(wordlist):
        current_row.append(1 if word in tokens else 0)

    rows.append(current_row)

data_model = pd.DataFrame(rows, columns=columns)
data_labels = pd.Series(labels)


bow = data_model

"""# **Classification**"""

import random    #Randomize the Texts
seed = 777
random.seed(seed)

def log(x):
    #can be used to write to log file
     print(x)

def test_classifier(X_train, y_train, X_test, y_test, classifier):
    log("")
    log("---------------------------------------------------------")
    log("Testing " + str(type(classifier).__name__))
    now = time()
    list_of_labels = sorted(list(set(y_train)))
    model = classifier.fit(X_train, y_train)
    log("Learing time {0}s".format(time() - now))
    now = time()
    predictions = model.predict(X_test)
    log("Predicting time {0}s".format(time() - now))

    # Calculate Accuracy, Precision, recall computation
    
    precision = precision_score(y_test, predictions, average=None, pos_label=None, labels=list_of_labels)
    recall = recall_score(y_test, predictions, average=None, pos_label=None, labels=list_of_labels)
    accuracy = accuracy_score(y_test, predictions)
    f1 = f1_score(y_test, predictions, average=None, pos_label=None, labels=list_of_labels)
    
    log("=================== Results ===================")
    log("         Negative   Positive          ")
    log("F1       " +   str(f1))
    log("Precision" +   str(precision))
    log("Recall   " +   str(recall))
    log("Accuracy " +   str(accuracy))
    log("===============================================")

    return precision, recall, accuracy, f1

def cv(classifier, X_train, y_train):
    log("===============================================")
    classifier_name = str(type(classifier).__name__)
    now = time()
    log("Crossvalidating " + classifier_name + "...")
    accuracy = [cross_val_score(classifier, X_train, y_train, cv=8, n_jobs=-1)]
    log("Crosvalidation completed in {0}s".format(time() - now))
    log("Accuracy: " + str(accuracy[0]))
    log("Average accuracy: " + str(np.array(accuracy[0]).mean()))
    log("===============================================")
    return accuracy

train_data.columns

dat1 = train_data
dat2 = data_model

dat1 = dat1.reset_index(drop=True)
dat2 = dat2.reset_index(drop=True)

data_model = dat1.join(dat2)

data_model = data_model.drop(columns=['ID', 'Text', 'Sentiment', 'tokenized', 'stremming'], axis=1)

"""# **Naive Bayes**"""

from sklearn.naive_bayes import BernoulliNB  #Print f1, Precision, Recall ,Accuracy Score got Negatives and Positives Posts
X_train, X_test, y_train, y_test = train_test_split(bow.iloc[:, 1:], bow['label'], test_size=0.3)
precision, recall, accuracy, f1 = test_classifier(X_train, y_train, X_test, y_test, BernoulliNB())

bn_acc = cv( BernoulliNB(),data_model.drop(columns='label',axis=1), data_model['label'])

"""# **Random Forest**"""

from sklearn.ensemble import RandomForestClassifier
X_train, X_test, y_train, y_test = train_test_split(data_model.drop(columns='label',axis=1),data_model['label'] , test_size=0.3)
precision, recall, accuracy, f1 = test_classifier(X_train, y_train, X_test, y_test, RandomForestClassifier(random_state=seed,n_estimators=403,n_jobs=-1))

rf_acc = cv(RandomForestClassifier(n_estimators=403,n_jobs=-1, random_state=seed),data_model.drop(columns='label',axis=1), data_model['label'])

"""# **XGBoost**"""

from xgboost import XGBClassifier as XGBoostClassifier
X_train, X_test, y_train, y_test = train_test_split(data_model.drop(columns='label',axis=1),data_model['label'] , test_size=0.3)
precision, recall, accuracy, f1 = test_classifier(X_train, y_train, X_test, y_test, XGBoostClassifier(seed=seed))

xg_acc = cv(XGBoostClassifier(seed=seed),data_model.drop(columns='label',axis=1), data_model['label'])

"""# **Test Data**"""

test_data.head()

test_data.columns

test_data = test_data[test_data['Text'] != ""]

# Drop null values
test_data = test_data.dropna() 


# Clean tweets
test_data['Text'] = test_data['Text'].apply(clean_tweets)

## Tokenize data
test_data['tokenized'] = test_data['Text'].apply(tokenize)
test_data['stremming'] = test_data['tokenized'].apply(stemming)

test_data.columns

def word_listest(processed_data): # wORDLIST FUNCTION FOR ANALYZE MOST COMMON WORDS WITH PURPOSE TO IDENTIFY OUR APP THE REAL SENTIMENT
    #print(processed_data)
    min_occurrences=3 
    max_occurences=500 
    stopwords=nltk.corpus.stopwords.words("english")
    whitelist = ["n't","not"]
    wordlist = []
    
    whitelist = whitelist if whitelist is None else whitelist
    
    words = Counter()
    for idx in processed_data.index:
        words.update(processed_data.loc[idx, "tokenized"])

    for idx, stop_word in enumerate(stopwords):
        if stop_word not in whitelist:
            del words[stop_word]
    #print(words)

    word_df = pd.DataFrame(data={"word": [k for k, v in words.most_common() if min_occurrences < v < max_occurences],
                                 "occurrences": [v for k, v in words.most_common() if min_occurrences < v < max_occurences]},
                           columns=["word", "occurrences"])
    #print(word_df)
    word_df.to_csv("wordlistest.csv", index_label="idx")
    wordlist = [k for k, v in words.most_common() if min_occurrences < v < max_occurences]
    #print(wordlist)

# wordlistest
word_listest(test_data)

words = pd.read_csv("wordlistest.csv") #CREATE WORDLIST TEST CSV WITH THE MOST COMMON WORDS

## BAG OF WORDS
wordlist= []
if os.path.isfile("wordlistest.csv"):
    word_df = pd.read_csv("wordlistest.csv")
    word_df = word_df[word_df["occurrences"] > 3]
    wordlist = list(word_df.loc[:, "word"])

label_column = ["label"]
columns = label_column + list(map(lambda w: w + "_bow",wordlist))
labels = []
rows = []
for idx in test_data.index:
    current_row = []
        # add label
    current_label = test_data.loc[idx, "Text"]
    labels.append(current_label)
    current_row.append(current_label)

    # add bag-of-words
    tokens = set(test_data.loc[idx, "tokenized"])
    for _, word in enumerate(wordlist):
        current_row.append(1 if word in tokens else 0)

    rows.append(current_row)

data_model = pd.DataFrame(rows, columns=columns)
data_labels = pd.Series(labels)

dat1 = test_data
dat2 = data_model

dat1 = dat1.reset_index(drop=True)
dat2 = dat2.reset_index(drop=True)

data_model = dat1.join(dat2)

test_model = pd.DataFrame()

data_model.columns
test_model['original_id'] = data_model['ID']

data_model = data_model.drop(columns=['ID', 'Text', 'Sentiment', 'tokenized', 'stremming'], axis=1)

from sklearn.ensemble import RandomForestClassifier

RF = RandomForestClassifier(n_estimators=403,max_depth=10)

RF.fit(data_model.drop(columns='label',axis=1),data_model['label'])

predictions = RF.predict(data_model.drop(columns='label',axis=1))

results = pd.DataFrame([],columns=["ID","Category"])
results["ID"] = test_model["original_id"]
results["Category"] = predictions
results.to_csv("results_xgb.csv",index=False)

"""# **Input Tweet & Analyzing Sentiment Polarity for understanding the Sentiment**"""

# Give text input for testing your post!
# After clean tweet and print it!

y= input("Type your post for analysis:")
x=clean_tweets(y)
print(x)

# Using textblob library for data analysis 
# After sentiment and polarity for calculate the emotion of the post and print it for testing!
text= TextBlob(y)


z = text.sentiment.polarity

print (z)

# Using if statement for printing if it is positive or negative!

if z==0: 
    print("Neutral")
elif z<0:
    print("Negative")
else:
    print("Positive")
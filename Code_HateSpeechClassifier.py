# -*- coding: utf-8 -*-
"""Assignment 2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ew8Hm8XP6Iwj9NQJSeKKPr61erdgm9x8

#                                     TASK -- 1
"""

import pandas as pd
import numpy as np

df = pd.read_csv("NLP_ass_train.tsv", sep='\t',header=None)
df.columns = ['text', 'type']
df.head()

df_val = pd.read_csv("NLP_ass_valid.tsv", sep='\t',header=None)
df_val.columns = ['text', 'type']
df_val.head()

df_test = pd.read_csv("NLP_ass_test.tsv", sep='\t',header=None)
df_test.columns = ['text', 'type']
df_test.head()

import nltk
import re
from nltk.stem.snowball import SnowballStemmer
from nltk.stem  import  WordNetLemmatizer
from nltk.corpus import stopwords

stop_words=stopwords.words('english')
lemmatizer = WordNetLemmatizer()
snow_stemmer = SnowballStemmer(language='english')

def preprocessor(text):
    text=text.split()
    text=[snow_stemmer.stem(w) for w in text]
    text=[lemmatizer.lemmatize(w,pos="a") for w in text]
    text=[w  for w in text if not w in stop_words]
    text=' '.join(text)
    text = re.sub(r'[^A-Za-z1-9 ]', ' ', text)
    return text
df['text']=df['text'].apply(preprocessor)
df.head()

import nltk
nltk.download('wordnet')

from gensim.models import KeyedVectors
from gensim import models

word2vec_path = 'GoogleNews-vectors-negative300.bin'
word2vec_model = models.KeyedVectors.load_word2vec_format(word2vec_path, binary=True)

from gensim.models import Word2Vec
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split


def get_input_features(dataframe):
    input_features = []
    for text in dataframe:
        # Initialize an empty array for the text
        feature_vector = np.zeros((word2vec_model.vector_size,))
        num_words = 0
        for word in text:
            if word in word2vec_model:
                feature_vector = np.add(feature_vector, word2vec_model[word])
                num_words += 1
        # Average the word vectors to get the feature vector for the text
        if num_words > 0:
            feature_vector = np.divide(feature_vector, num_words)
        input_features.append(feature_vector)

    # Convert input features and target labels to PyTorch tensors
    input_features = torch.tensor(input_features, dtype=torch.float32)
    return input_features

input_features=get_input_features(df['text'])
# target_labels=['normal','hatespeech','offensive']
target_labels=df['type'].map( {'normal': 0, 'hatespeech': 1, 'offensive': 2} ).astype(int)
target_labels = torch.tensor(target_labels, dtype=torch.long)

# Number of target classes in the dataset
num_classes = 3  # Specify the number of target classes

# Split data into training, validation, and test sets
X_train, y_train =input_features, target_labels

class NeuralNetwork(nn.Module):
    def __init__(self, input_size, hidden_size1, hidden_size2, output_size):
        super(NeuralNetwork, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size1)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size1, hidden_size2)
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(hidden_size2, output_size)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu1(x)
        x = self.fc2(x)
        x = self.relu2(x)
        x = self.fc3(x)
        x = self.softmax(x)
        return x

from tqdm import tqdm
# Initialize the model, loss function, and optimizer
input_size = word2vec_model.vector_size
hidden_size1 = 128
hidden_size2 = 64
output_size = num_classes

model = NeuralNetwork(input_size, hidden_size1, hidden_size2, output_size)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training the model
num_epochs = 100
batch_size = 32

train_dataset = TensorDataset(X_train, y_train)
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

for epoch in range(num_epochs):
    for inputs, labels in tqdm(train_loader):
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
#         print(loss)

X_val, y_val =df_val['text'],df_val['type'].map( {'normal': 0, 'hatespeech': 1, 'offensive': 2} ).astype(int)
y_val = torch.tensor(y_val, dtype=torch.long)
X_val=get_input_features(X_val)
# Evaluating the model on the validation set
with torch.no_grad():
    outputs = model(X_val)
    _, predicted = torch.max(outputs, 1)
    accuracy = torch.sum(predicted == y_val).item() / y_val.size(0)

print("Test Set Accuracy: {:.2f}%".format(accuracy * 100))

# Save the model
torch.save(model.state_dict(), 'best_model.pth')

"""# Accuracy using test data set"""

X_test, y_test =df_test['text'],df_test['type'].map( {'normal': 0, 'hatespeech': 1, 'offensive': 2} ).astype(int)
y_test = torch.tensor(y_test, dtype=torch.long)
X_test=get_input_features(X_test)
# Evaluating the model on the validation set
with torch.no_grad():
    outputs = model(X_test)
    _, predicted = torch.max(outputs, 1)
    accuracy = torch.sum(predicted == y_test).item() / y_test.size(0)

print("Test Set Accuracy: {:.2f}%".format(accuracy * 100))

"""#                                              TASK -- 2"""

import re
import nltk
import pandas as pd
import numpy as np
from nltk.corpus import stopwords
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

import nltk
nltk.download('punkt')
nltk.download('stopwords')

# Sample raw text data
df_train1 = pd.read_csv("NLP_ass_train.tsv", sep='\t',header=None)
df_train1.columns = ['text', 'type']
raw_text_data = df_train1['text']  # Your raw text data goes here
target_labels = df_train1['type'].map( {'normal': 0, 'hatespeech': 1, 'offensive': 2} ).astype(int)   # Your target labels go here

# Step 1: Data Preprocessing
def preprocess_text(text):
    # Remove unnecessary symbols
    text = re.sub(r'[^\w\s]', '', text)
    # Convert to lowercase
    text = text.lower()
    # Remove stop words
    stop_words = set(stopwords.words('english'))
    words = nltk.word_tokenize(text)
    words = [word for word in words if word not in stop_words]
    return words

# Preprocess the raw text data
processed_data = [preprocess_text(text) for text in raw_text_data]

# Step 2: Create Vocabulary
vocab = set(word for sentence in processed_data for word in sentence)

# Step 3: Define Maximum Sequence Length
max_seq_length = 50  # You can adjust this based on your dataset and task requirements

# Step 4: Tokenize and Pad/Truncate Sentences
word_to_idx = {word: idx + 1 for idx, word in enumerate(vocab)}
word_to_idx['<pad>'] = 0

def encode_sentence(sentence):
    encoded_sentence = [word_to_idx.get(word, 0) for word in sentence]
    # Pad or truncate the sentence to the maximum sequence length
    encoded_sentence = encoded_sentence[:max_seq_length] + [0] * (max_seq_length - len(encoded_sentence))
    return encoded_sentence

encoded_data = [encode_sentence(sentence) for sentence in processed_data]

# Step 5: load train, validation, and test sets
df_val1 = pd.read_csv("NLP_ass_valid.tsv", sep='\t',header=None)
df_val1.columns = ['text', 'type']
df_test1 = pd.read_csv("NLP_ass_test.tsv", sep='\t',header=None)
df_test1.columns = ['text', 'type']
df_val1['text']=[preprocess_text(text) for text in df_val1['text']]
df_test1['text']=[preprocess_text(text) for text in df_test1['text']]
X_train, y_train = encoded_data, target_labels
X_val,y_val = [encode_sentence(sentence) for sentence in df_val1['text']],df_val1['type'].map( {'normal': 0, 'hatespeech': 1, 'offensive': 2} ).astype(int)
X_test, y_test = [encode_sentence(sentence) for sentence in df_test1['text']],df_test1['type'].map( {'normal': 0, 'hatespeech': 1, 'offensive': 2} ).astype(int)

# Step 6: Define Dataloaders
class CustomDataset(Dataset):
    def __init__(self, data, labels):
        self.data = torch.tensor(data, dtype=torch.float)
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]

train_dataset = CustomDataset(X_train, y_train)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_dataset = CustomDataset(X_val, y_val)
val_loader = DataLoader(val_dataset, batch_size=32)

# Step 7: Define Model Class
class RNNClassifier(nn.Module):
    def __init__(self, vocab_size, embed_size, hidden_size, output_size, num_layers=1, dropout_prob=0.2):
        super(RNNClassifier, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_size)  #embedding layer
        self.rnn = nn.LSTM(embed_size, hidden_size, num_layers, batch_first=True, dropout=dropout_prob)   #rnn layer
        self.dropout = nn.Dropout(dropout_prob) # Setting dropout for reducing overfitting
        self.fc = nn.Linear(hidden_size, output_size)  #classification layer

    def forward(self, x):
        x = self.embedding(x)
        output, _ = self.rnn(x)
        output = output[:, -1, :]  # Use the last hidden state
        output = self.dropout(output)
        output = self.fc(output)
        return output

    def predict(self, x):
        # Apply softmax activation for predictions
        x = F.softmax(self.forward(x), dim=1)
        return x

# Step 8: Train the Model with Early Stopping
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# Number of target classes in the dataset
num_classes = 3  # Specify the number of target classes

model = RNNClassifier(vocab_size=len(vocab) + 1, embed_size=100, hidden_size=128, output_size=num_classes, num_layers=2, dropout_prob=0.2)
model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

patience = 5
best_val_loss = float('inf')
counter = 0

for epoch in range(50):  # You can adjust the number of epochs
    model.train()
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

    model.eval()
    val_loss = 0
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            val_loss += criterion(outputs, labels).item()

    val_loss /= len(val_loader)
    print(f'Epoch [{epoch+1}/50], Validation Loss: {val_loss:.4f}')

    if val_loss < best_val_loss:
        best_val_loss = val_loss
        counter = 0
        torch.save(model.state_dict(), 'best_rnn_model.pth')
    else:
        counter += 1
        if counter >= patience:
            print("Early stopping. Loading the best model weights.")
            break

# Step 9: Load Best Model Weights
model.load_state_dict(torch.load('best_rnn_model.pth'))

# Step 10: Evaluate Model on Test Set
model.eval()
test_dataset = CustomDataset(X_test, y_test)
test_loader = DataLoader(test_dataset, batch_size=32)
test_loss = 0
correct_predictions = 0

with torch.no_grad():
    for inputs, labels in test_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        outputs = model(inputs)
        test_loss += criterion(outputs, labels).item()
        _, predicted = torch.max(outputs, 1)
        correct_predictions += (predicted == labels).sum().item()

test_loss /= len(test_loader)
test_accuracy = correct_predictions / len(y_test)

print(f'Test Loss: {test_loss:.4f}, Test Accuracy: {test_accuracy * 100:.2f}%')

"""# TASK-3"""

# Transformers installation
! pip install transformers
# To install from source instead of the last release, comment the command above and uncomment the following one.
# ! pip install git+https://github.com/huggingface/transformers.git

import re
import nltk
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertForSequenceClassification, AdamW
from sklearn.model_selection import train_test_split
from nltk.corpus import stopwords
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

import nltk
nltk.download('stopwords')
nltk.download('punkt')

num_classes=3
# Sample raw text data
df_train1 = pd.read_csv("NLP_ass_train.tsv", sep='\t',header=None)
df_train1.columns = ['text', 'type']
raw_text_data = df_train1['text']  # Your raw text data goes here
target_labels = df_train1['type'].map( {'normal': 0, 'hatespeech': 1, 'offensive': 2} ).astype(int)   # Your target labels go here

# Step 1: Data Preprocessing
def preprocess_text(text):
    # Remove unnecessary symbols
    text = re.sub(r'[^\w\s]', '', text)
    # Convert to lowercase
    text = text.lower()
    # Remove stop words
    stop_words = set(stopwords.words('english'))
    words = nltk.word_tokenize(text)
    words = [word for word in words if word not in stop_words]
    return ' '.join(words)

# Preprocess the raw text data
processed_data = [preprocess_text(text) for text in raw_text_data]

from transformers import AutoTokenizer,AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased",
                                                           problem_type="multi_label_classification",
                                                           num_labels=num_classes,
                                                           )

# Step 3: Dataloader Class
class CustomDataset(Dataset):
    def __init__(self, texts, labels):
        self.texts = texts
        self.labels = labels

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        return {'text': self.texts[idx], 'label': self.labels[idx]}

# Step 4: Create Model Class
class CustomBERTClassifier(nn.Module):
    def __init__(self, bert_model, num_classes, dropout_prob=0.2):
        super(CustomBERTClassifier, self).__init__()
        self.bert = bert_model
        self.dropout = nn.Dropout(dropout_prob)
        self.classifier = nn.Linear(self.bert.config.hidden_size, num_classes)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids, attention_mask=attention_mask)
        pooled_output = outputs['pooler_output']
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        return logits

# Step 5: Train Loop, Optimizers, Schedulers, Loss Function
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)
optimizer = AdamW(model.parameters(), lr=2e-5)
criterion = nn.CrossEntropyLoss()

# Step 5: load train, validation, and test sets
df_val1 = pd.read_csv("NLP_ass_valid.tsv", sep='\t',header=None)
df_val1.columns = ['text', 'type']
df_test1 = pd.read_csv("NLP_ass_test.tsv", sep='\t',header=None)
df_test1.columns = ['text', 'type']
df_val1['text']=[preprocess_text(text) for text in df_val1['text']]
df_test1['text']=[preprocess_text(text) for text in df_test1['text']]
X_train, y_train = processed_data, target_labels
X_val,y_val =df_val1['text'],df_val1['type'].map( {'normal': 0, 'hatespeech': 1, 'offensive': 2} ).astype(int)
X_test, y_test = df_test1['text'],df_test1['type'].map( {'normal': 0, 'hatespeech': 1, 'offensive': 2} ).astype(int)

train_dataset = CustomDataset(X_train, y_train)
train_loader = DataLoader(train_dataset, batch_size=512, shuffle=True)

val_dataset = CustomDataset(X_val, y_val)
val_loader = DataLoader(val_dataset, batch_size=512)

test_dataset = CustomDataset(X_test, y_test)
test_loader = DataLoader(test_dataset, batch_size=512)

# Step 7: Train the Model with Early Stopping
patience = 5
best_val_loss = float('inf')
counter = 0

for epoch in range(50):  # You can adjust the number of epochs
    model.train()
    # Inside the training loop
    for batch in train_loader:
        input_texts = batch['text']
        labels = batch['label'].long()  # Convert labels to torch.long data type
        inputs = tokenizer(input_texts, padding=True, truncation=True, return_tensors='pt')
        inputs = {key: value.to(device) for key, value in inputs.items()}
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(**inputs)
        logits = outputs.logits
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()


    model.eval()
    val_loss = 0
    with torch.no_grad():
        for batch in val_loader:
            input_texts = batch['text']
            labels = batch['label']
            inputs = tokenizer(input_texts, padding=True, truncation=True, return_tensors='pt')
            inputs = {key: value.to(device) for key, value in inputs.items()}
            labels = labels.to(device)

            outputs = model(**inputs)
            logits = outputs.logits
            val_loss += criterion(logits, labels).item()

    val_loss /= len(val_loader)
    print(f'Epoch [{epoch+1}/50], Validation Loss: {val_loss:.4f}')

    if val_loss < best_val_loss:
        best_val_loss = val_loss
        counter = 0
        torch.save(model.state_dict(), 'best_bert_model.pth')
    else:
        counter += 1
        if counter >= patience:
            print("Early stopping. Loading the best model weights.")
            break

# Step 8: Load Best Model Weights
model.load_state_dict(torch.load('best_bert_model.pth'))

# Step 9: Evaluate Model on Test Set
model.eval()
test_loss = 0
correct_predictions = 0

with torch.no_grad():
    for batch in test_loader:
        input_texts = batch['text']
        labels = batch['label']
        inputs = tokenizer(input_texts, padding=True, truncation=True, return_tensors='pt')
        inputs = {key: value.to(device) for key, value in inputs.items()}
        labels = labels.to(device)

        outputs = model(**inputs)
        logits = outputs.logits
        test_loss += criterion(logits, labels).item()
        _, predicted = torch.max(logits, 1)
        correct_predictions += (predicted == labels).sum().item()

test_loss /= len(test_loader)
test_accuracy = correct_predictions / len(y_test)

print(f'Test Loss: {test_loss:.4f}, Test Accuracy: {test_accuracy * 100:.2f}%'




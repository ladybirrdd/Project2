import tensorflow as tf
import numpy as np
import pickle
import unicodedata
import re
import os

with open('inp_lang_tokenizer.pkl', 'rb') as f:
    inp_lang = pickle.load(f)

with open('targ_lang_tokenizer.pkl', 'rb') as f:
    targ_lang = pickle.load(f)

embedding_dim = 256
units = 1024
vocab_inp_size = len(inp_lang.word_index) + 1
vocab_tar_size = len(targ_lang.word_index) + 1
max_length_inp = 50
max_length_targ = 50

def unicode_to_ascii(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

def preprocess_sentence(w: str) -> str:
    w = unicode_to_ascii(w.lower().strip())
    w = re.sub(r"([?.!,¿])", r" \1 ", w)
    w = re.sub(r'[" "]+', " ", w)
    w = re.sub(r"[^a-zA-Z\u0900-\u097f?.!,¿]+", " ", w)
    w = ' '.join(w.strip().split())
    return '<start> ' + w + ' <end>'

inp_lang.word_index.setdefault('<unk>', len(inp_lang.word_index) + 1)

class Encoder(tf.keras.Model):
    def __init__(self, vocab_size, embedding_dim, enc_units, batch_sz):
        super().__init__()
        self.batch_sz = batch_sz
        self.enc_units = enc_units
        self.embedding = tf.keras.layers.Embedding(vocab_size, embedding_dim)
        self.gru = tf.keras.layers.GRU(enc_units,
                                       return_sequences=True,
                                       return_state=True,
                                       recurrent_initializer='glorot_uniform',
                                       reset_after=False)

    def call(self, x, hidden):
        x = self.embedding(x)
        output, state = self.gru(x, initial_state=hidden)
        return output, state

    def initialize_hidden_state(self):
        return tf.zeros((self.batch_sz, self.enc_units))

class BahdanauAttention(tf.keras.layers.Layer):
    def __init__(self, units):
        super().__init__()
        self.W1 = tf.keras.layers.Dense(units)
        self.W2 = tf.keras.layers.Dense(units)
        self.V = tf.keras.layers.Dense(1)

    def call(self, query, values):
        query_with_time_axis = tf.expand_dims(query, 1)
        score = self.V(tf.nn.tanh(self.W1(query_with_time_axis) + self.W2(values)))
        attention_weights = tf.nn.softmax(score, axis=1)
        context_vector = attention_weights * values
        context_vector = tf.reduce_sum(context_vector, axis=1)
        return context_vector, attention_weights

class Decoder(tf.keras.Model):
    def __init__(self, vocab_size, embedding_dim, dec_units, batch_sz):
        super().__init__()
        self.batch_sz = batch_sz
        self.dec_units = dec_units
        self.embedding = tf.keras.layers.Embedding(vocab_size, embedding_dim)
        self.gru = tf.keras.layers.GRU(dec_units,
                                       return_sequences=True,
                                       return_state=True,
                                       recurrent_initializer='glorot_uniform',
                                       reset_after=False)
        self.fc = tf.keras.layers.Dense(vocab_size)
        self.attention = BahdanauAttention(dec_units)

    def call(self, x, hidden, enc_output):
        context_vector, attention_weights = self.attention(hidden, enc_output)
        x = self.embedding(x)
        x = tf.concat([tf.expand_dims(context_vector, 1), x], axis=-1)
        output, state = self.gru(x)
        x = self.fc(tf.reshape(output, (-1, output.shape[2])))
        return x, state, attention_weights

def build_models_and_restore():
    encoder = Encoder(vocab_inp_size, embedding_dim, units, 1)
    decoder = Decoder(vocab_tar_size, embedding_dim, units, 1)
    
    # Warm-up call
    dummy_input = tf.zeros((1, max_length_inp), dtype=tf.int32)
    encoder_hidden = encoder.initialize_hidden_state()
    enc_out, enc_hidden = encoder(dummy_input, encoder_hidden)
    _ = decoder(tf.zeros((1, 1), dtype=tf.int32), enc_hidden, enc_out)

    checkpoint = tf.train.Checkpoint(encoder=encoder, decoder=decoder)
    checkpoint.restore(tf.train.latest_checkpoint('./checkpoints')).expect_partial()
    return encoder, decoder

encoder, decoder = build_models_and_restore()

def evaluate(sentence: str) -> str:
    sentence = preprocess_sentence(sentence)
    inputs = [inp_lang.word_index.get(word, inp_lang.word_index['<unk>']) for word in sentence.split()]
    inputs = tf.keras.preprocessing.sequence.pad_sequences([inputs], maxlen=max_length_inp, padding='post')
    inputs = tf.convert_to_tensor(inputs)

    result = ''
    hidden = [tf.zeros((1, units))]
    enc_out, enc_hidden = encoder(inputs, hidden)

    dec_hidden = enc_hidden
    dec_input = tf.expand_dims([targ_lang.word_index['<start>']], 0)

    for _ in range(max_length_targ):
        predictions, dec_hidden, _ = decoder(dec_input, dec_hidden, enc_out)
        predicted_id = tf.argmax(predictions[0]).numpy()
        predicted_word = targ_lang.index_word.get(predicted_id, '<unk>')

        if predicted_word == '<end>':
            break
        result += predicted_word + ' '
        dec_input = tf.expand_dims([predicted_id], 0)

    return result.strip()

def translate_sentence(text: str) -> str:
    return evaluate(text)

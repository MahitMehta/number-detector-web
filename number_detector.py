from PIL import Image
from binascii import a2b_base64
import numpy as np
import json
from matplotlib import pyplot as plt
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("./service_account.json")
app = firebase_admin.initialize_app(cred)
db = firestore.client()


def get_data():
    docRef = db.collection("weights").document("weights-public-web")
    doc = docRef.get()
    data = doc.to_dict()
    weights = json.loads(data["weights"])
    adjustedCount = data["adjustedCount"]
    return [weights, adjustedCount]


class Activation_Sigmoid:
    def forward(self, x):
        self.output = 1 / (1 + np.exp(-x))


class Layer_Dense:
    def __init__(self, input_neurons, output_neurons):
        self.weights, self.adjustedCount = get_data()
        self.input_neurons = input_neurons
        self.output_neurons = output_neurons
        self.biases = np.zeros(output_neurons)

    def forward(self, x):
        self.output = np.dot(x, self.weights) + self.biases


class Train:
    def __init__(self, inputs, example_outputs):
        self.inputs = inputs
        self.example_outputs = example_outputs
        _, in_neurons = self.inputs.shape
        _, out_neurons = self.example_outputs.shape
        self.layer = Layer_Dense(in_neurons, out_neurons)
        self.adjustedCount = self.layer.adjustedCount

    def sigmoid_derivative(self, x):
        return x * (1 - x)

    def basic(self, count=1000):
        for i in range(count):
            self.layer.forward(self.inputs)
            activation_sigmoid = Activation_Sigmoid()
            activation_sigmoid.forward(self.layer.output)
            current_outputs = activation_sigmoid.output
            correct_outputs = self.example_outputs
            error = correct_outputs - current_outputs
            adjustments = error * self.sigmoid_derivative(current_outputs)
            self.layer.weights += np.dot(np.array(self.inputs).T, adjustments)
        return self.layer.weights


class Number_Detector:
    def __init__(self, dataURL):
        self.dataURL = dataURL

    def cvt_Image(self):
        binary_data = a2b_base64(self.dataURL)
        with open("input_image.png", "wb") as file:
            file.write(binary_data)
        im = Image.open("input_image.png").convert('L')
        newImage = Image.new('L', (28, 28), (255))
        img = im.resize((28, 28))
        newImage.paste(img)

        tv = list(newImage.getdata())
        tva = [(255 - x) * 1.0 / 255.0 for x in tv]
        saveOutput = False
        if saveOutput:
            newImage.save("output_image.png")
        self.input_data = 1 - np.array(tva)

    def detect_number(self):
        PIXEL_COUNT = 784
        layer_one = Layer_Dense(PIXEL_COUNT, 10)
        input_data = self.input_data
        layer_one.forward(input_data)
        output = layer_one.output
        activation_one = Activation_Sigmoid()
        activation_one.forward(output)
        activation_function_output = activation_one.output
        maxOutput = np.max(activation_function_output)
        for idx, num in enumerate(activation_function_output):
            if num == maxOutput:
                guess = idx

        showImage = False

        if showImage:
            im = input_data.reshape(28, 28)
            pixels = im.reshape((28, 28))
            plt.imshow(pixels)
            plt.show()

        return guess

    def train_detector(self, label):
        input_data = np.array([self.input_data])
        example_outputs = np.zeros((1, 10))
        example_outputs[0][label] = 1
        train = Train(
            input_data, example_outputs)
        trained_weights = train.basic()
        adjustedCount = train.adjustedCount
        adjustedCount += 1
        lists = trained_weights.tolist()
        json_str = json.dumps(lists)
        data = {"weights": json_str, "adjustedCount": adjustedCount}
        db.collection('weights').document('weights-public-web').set(data)

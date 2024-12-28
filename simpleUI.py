import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton

from GrassDetectionAndAreaCalculation import  mainProcessingFunction

#Implementation of the simple UI

class SimpleWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CuraTurf")
        self.resize(400, 600)
        # Create two labels and input fields
        self.label1 = QLabel("Address")
        #self.label1.setFixedSize(250, 50)
        self.text_input1 = QLineEdit()

        self.text_input1.setFixedSize(300,50)

        self.label2 = QLabel("City")
        self.text_input2 = QLineEdit()
        self.text_input2.setFixedSize(300, 50)


        self.label3 = QLabel("State")
        self.text_input3 = QLineEdit()
        self.text_input3.setFixedSize(300, 50)

        self.label4 = QLabel("Zip code")
        self.text_input4 = QLineEdit()
        self.text_input4.setFixedSize(300, 50)

        self.label5 = QLabel("Country")
        self.text_input5 = QLineEdit()
        self.text_input5.setFixedSize(300, 50)

        self.label6 = QLabel("Minimum sq ft")
        self.text_input6 = QLineEdit()
        self.text_input6.setFixedSize(300, 50)

        self.label7 = QLabel("Radius(in miles)")
        self.text_input7 = QLineEdit()
        self.text_input7.setFixedSize(300, 50)

        self.label8 = QLabel("API Key")
        self.text_input8 = QLineEdit()
        self.text_input8.setFixedSize(300, 50)


        # Create a push button
        self.button = QPushButton("Export .CSV")
        self.button.clicked.connect(self.on_button_click)
        self.button.setFixedSize(400,50)
        self.button.setStyleSheet("background-color: green")

        # Set up the layout
        layout = QVBoxLayout()

        # First row (label and input 1)
        row1 = QHBoxLayout()


        row1.addWidget(self.label1)
        row1.addWidget(self.text_input1)

        # Second row (label and input 2)
        row2 = QHBoxLayout()
        row2.addWidget(self.label2)
        row2.addWidget(self.text_input2)

        row3 = QHBoxLayout()
        row3.addWidget(self.label3)
        row3.addWidget(self.text_input3)

        row4 = QHBoxLayout()
        row4.addWidget(self.label4)
        row4.addWidget(self.text_input4)

        row5 = QHBoxLayout()
        row5.addWidget(self.label5)
        row5.addWidget(self.text_input5)

        row6 = QHBoxLayout()
        row6.addWidget(self.label6)
        row6.addWidget(self.text_input6)

        row7 = QHBoxLayout()
        row7.addWidget(self.label7)
        row7.addWidget(self.text_input7)

        row8 = QHBoxLayout()
        row8.addWidget(self.label8)
        row8.addWidget(self.text_input8)



        # Add rows and button to the layout
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)
        layout.addLayout(row4)
        layout.addLayout(row5)
        layout.addLayout(row6)
        layout.addLayout(row7)
        layout.addLayout(row8)
        layout.addWidget(self.button)

        # Set the window layout
        self.setLayout(layout)

    def on_button_click(self):
        # Print the text from input fields
        #print("Input 1:", self.text_input1.text())
        #print("Input 2:", self.text_input2.text())
        finalAddress = self.text_input1.text() + ', ' + self.text_input2.text()  + ', ' + self.text_input3.text() + ', ' +  self.text_input4.text() + ', '  + self.text_input5.text()
        minumumSquare = float(self.text_input6.text())
        radius = float(self.text_input7.text())
        apiKey = self.text_input8.text()
       # mainProcessingFunction()
        mainProcessingFunction(finalAddress, radius, minumumSquare, apiKey)
        print("FInal address  ", finalAddress  )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleWindow()
    window.show()
    sys.exit(app.exec_())
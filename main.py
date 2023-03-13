from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pyqtgraph as pg
import sys
import traceback
import time
import opcua
import interface
from PyQt5.QtCore import pyqtSignal, QTimer, QObject, QSettings
import csv
from datetime import datetime

class WorkerSignals(QObject):
    # Lấy tín hiệu từ luồng worker
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class  Worker(QRunnable):
    # Tạo class Worker kế thừa từ class QRunnable để thiết lập luồng xử lý tín hiệu và kết thúc
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs['progress_callback'] = self.signals.progress
    @pyqtSlot()
    def run(self):
        # Khởi tạo hàm chạy. Các hàm cần thực thi ở luồng worker sẽ chạy ở hàm này
        try:
            result = self.fn(*self.args)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()

class MainWindow(QMainWindow, interface.Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.threadpool = QThreadPool()

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_barchart)
        self.timer.start()
        self.btn_connect.clicked.connect(self.connect_opc_server)
        self.btn_connect.clicked.connect(self.link_slot)
        self.btn_disconnect.clicked.connect(self.disconnect_opc_server)
        self.btn_main_valve.clicked.connect(self.control_valve)
        self.btn_bulb_1.clicked.connect(self.control_bulb_1)
        self.btn_bulb_2.clicked.connect(self.control_bulb_2)
        self.le_url.setText("opc.tcp://127.0.0.1:12345")
  
     
        self.settings = QSettings()


        # Khởi tạo dữ liệu trục x, y cho các biểu
        self.x_time = [0]
        self.y_pressure = [0]
        self.y_flow_rate = [0]
        self.accum_flow = [0]

        self.y_temp = [0]

        # Khởi tạo màu cho các đường thể hiện dữ liệu
        pen_1 = pg.mkPen(color=(128, 255, 0),width = 2)
        pen_2 = pg.mkPen(color=(0, 0, 255), width = 2)
        pen_3 = pg.mkPen(color='red', width = 2)
        # Khởi tạo các biểu đồ tương ứng
        self.data_pressure = self.graphicsView_pressure.plot(self.x_time, self.y_pressure,pen=pen_1,name = "Pressure (Kpa)")
        self.data_flow_rate = self.graphicsView_flow_rate.plot(self.x_time, self.y_flow_rate,pen=pen_2,name = "Flow rate (L/min)")
        self.data_temp = self.graphicsView_temp.plot(self.x_time, self.y_temp,pen=pen_3, name = "Temperatue (°C)")

    def connect_opc_server(self):
        # Khởi tạo giá trị để kết nối tới server
        url = self.le_url.text()
        global client, temp_node, pressure_node, flow_node, main_valve_node, bulb_1_node, bulb_2_node
        client = opcua.Client(url, timeout=60)
        try:
            client.connect()
            self.lb_status.setText("Status: Connected.")
            sensors_node = client.get_objects_node().get_children()[1]
            temp_node = sensors_node.get_children()[0]
            pressure_node = sensors_node.get_children()[1]
            flow_node = sensors_node.get_children()[2]
            digital_node = client.get_objects_node().get_children()[2]
            main_valve_node = digital_node.get_children()[0]
            bulb_1_node = digital_node.get_children()[1]
            bulb_2_node = digital_node.get_children()[2]
        except:
           self.messege_box_warning()

    def get_data(self):
        temp = client.get_node(temp_node)
        press = client.get_node(pressure_node)
        flow = client.get_node(flow_node)
        main_valve = client.get_node(main_valve_node)
        bulb_1 = client.get_node(bulb_1_node)
        bulb_2 = client.get_node(bulb_2_node)
        with open("python_datas.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(['Time','Flow Rate','Pressure','Accumulation Flow','Temperature'])
        while True:
            a = 0
            if main_valve.get_value() == False:
                self.btn_main_valve.setText("Main Valve OFF")
                self.btn_main_valve.setStyleSheet("background-color: red")
            else:
                self.btn_main_valve.setText("Main Valve ON")
                self.btn_main_valve.setStyleSheet("background-color: green")
            if bulb_1.get_value() == False:
                self.btn_bulb_1.setText("Bulb 1 OFF")
                self.btn_bulb_1.setStyleSheet("background-color: red")
            else:
                self.btn_bulb_1.setText("Bulb 1 ON")
                self.btn_bulb_1.setStyleSheet("background-color: green")
            if bulb_2.get_value() == False:
                self.btn_bulb_2.setText("Bulb 2 OFF")
                self.btn_bulb_2.setStyleSheet("background-color: red")
            else:
                self.btn_bulb_2.setText("Bulb 2 ON")
                self.btn_bulb_2.setStyleSheet("background-color: green")
            temperature = temp.get_value()
            flow_rate = flow.get_value()
            pressure = press.get_value()

            self.x_time.append(self.x_time[-1]+1)
            self.y_pressure.append(pressure)
            self.y_flow_rate.append(flow_rate)
            self.y_temp.append(temperature)
            self.accum_flow.append(flow_rate/60)
            for i in self.accum_flow:
                a+=i
            if len(self.x_time) > 50:
                self.x_time = self.x_time[1:]
                self.y_pressure = self.y_pressure[1:]
                self.y_flow_rate = self.y_flow_rate[1:]
                self.y_temp = self.y_temp[1:]
            
            self.data_pressure.setData(self.x_time,self.y_pressure)
            self.data_flow_rate.setData(self.x_time,self.y_flow_rate)
            self.data_temp.setData(self.x_time,self.y_temp)

            self.lcd_temp.display('{:.02f}'.format(temperature))
            self.lcd_pressure.display(pressure)
            self.lcd_flow_rate.display(flow_rate)
            self.lcd_accumflow.display(a)

         # Ghi giá trị vào file 'csv'
            now = datetime.now().strftime("%H:%M:%S")  
            row  = [now,pressure,flow_rate,a,temperature]
            with open('python_datas.csv',"a") as f:
                writer = csv.writer(f)
                writer.writerow(row)
            time.sleep(1)
    
    def update_barchart(self):
        c = 0
        for i in self.accum_flow:
                c += i           
        b = [f'Accumulation Flow: {round(c,2)} L']
        x_axis = list(range(1,len(b)+1))
        ticks = []
        for i, item in enumerate(b):
            ticks.append((x_axis[i], item))
        ticks = [ticks]
        bargraph = pg.BarGraphItem(x = x_axis, height = c, width = 0.2, brush = 'green')
        self.graphicsView_accumflow.addItem(bargraph)
        ax = self.graphicsView_accumflow.getAxis('bottom')
        ax.setTicks(ticks)
    def control_valve(self):
        main_valve = client.get_node(main_valve_node)
        if main_valve.get_value() == False:
            self.btn_main_valve.setStyleSheet("background-color: green")
            main_valve.set_value(True)
        else:
            main_valve.set_value(False)
            self.btn_main_valve.setStyleSheet("background-color: red")
    def control_bulb_1(self):
        bulb_1 = client.get_node(bulb_1_node)
        if bulb_1.get_value() == False:
            bulb_1.set_value(True)
            self.btn_bulb_1.setStyleSheet("background-color: green")
        else:
            bulb_1.set_value(False)
            self.btn_bulb_1.setStyleSheet("background-color: red")
    def control_bulb_2(self):
        bulb_2 = client.get_node(bulb_2_node)
        if bulb_2.get_value() == False:
            bulb_2.set_value(True)
            self.btn_bulb_2.setStyleSheet("background-color: green")
        else:
            bulb_2.set_value(False)
            self.btn_bulb_2.setStyleSheet("background-color: red")
    def disconnect_opc_server(self): # Ngắt kết nối khỏi server
        try:
            client.disconnect()
            self.lb_status.setText("Status: Disconnect")
        except:
            self.messege_box_information()
    
    def messege_box_warning(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Warning")
        msg.setText("Check again URL Server !")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        retval = msg.exec_()
    def messege_box_information(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Information")
        msg.setText("Disconnected to server !")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        retval = msg.exec_()
    def link_slot(self):
        # Tạo một luồng để xử lý tín hiệu
        try:
            worker = Worker(self.get_data)
            self.threadpool.start(worker)
        except:
            pass
      
if __name__ == '__main__':
    window  = QApplication(sys.argv)
    app = MainWindow()
    app.show()
    window.exec_()
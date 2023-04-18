import numpy as np
from pyqtgraph.Qt import QtCore
import nidaqmx
from nidaqmx.stream_writers import AnalogMultiChannelWriter


class SignalWriter(QtCore.QThread):
    def __init__(self, x_offset=0, y_offset=0, z_offset=0):
        super(SignalWriter, self).__init__()  # 继承父类Qthread

        self.channel_name = "Dev1"
        self.writechannel_list = [0, 1, 2]
        self.channel_rate = 8000
        self.writechunksize = 100

        self.x = x_offset
        self.y = y_offset
        self.z = z_offset

        self.output = np.zeros([len(self.writechannel_list), self.writechunksize])
        self.running = False

    def generate_wave(self):
        output = np.array([
            self.x*np.ones(self.writechunksize),
            self.y*np.ones(self.writechunksize),
            self.z*np.ones(self.writechunksize)
        ])
        return output

    def run(self):
        """在调用thread的start的方法的时候会进行调用"""
        self.running = True
        self.writeTask = nidaqmx.Task()  # 实例化
        ao_args = {'min_val': -10,
                   'max_val': 10}
        for index, i in enumerate(self.writechannel_list):
            channel_string = self.channel_name + '/' + f'ao{i}'
            try:
                self.writeTask.ao_channels.add_ao_voltage_chan(channel_string, **ao_args)
            except Exception as e:
                if index == 0:
                    print('Could not open write channels. Are device names correct?')
                    return

        self.writeTask.timing.cfg_samp_clk_timing(
            rate=self.channel_rate,
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)

        # Set more properties for continuous signal modulation
        self.writeTask.out_stream.regen_mode = nidaqmx.constants.RegenerationMode.DONT_ALLOW_REGENERATION
        self.writeTask.out_stream.output_buf_size = 2 * self.writechunksize

        self.writeTask.register_every_n_samples_transferred_from_buffer_event(
            sample_interval=self.writechunksize,
            callback_method=self.add_more_data)

        self.writer = AnalogMultiChannelWriter(self.writeTask.out_stream)

        self.output = self.generate_wave()
        # self.output = 1.0*self.output

        try:
            self.writer.write_many_sample(data=self.output)
        except:
            print(self.output)
            print('Could not write data to the output')
            return

        self.writer.write_many_sample(data=self.output)  # 写入缓存区

        self.writeTask.start()

    def add_more_data(self, task_handle, every_n_samples_event_type, number_of_samples, callback_data):
        if self.running is True:
            self.output = self.generate_wave()
            # self.writer.write_many_sample(data=self.output)
        else:
            self.writeTask.close()
        return 0









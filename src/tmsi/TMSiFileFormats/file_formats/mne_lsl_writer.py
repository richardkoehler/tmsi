"""
The original file has been modified by Richard Köhler.

Copyright 2021 John Veillette (https://gitlab.com/john-veillette)
(c) 2022 Twente Medical Systems International B.V., Oldenzaal The Netherlands

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

#######  #     #   #####   #
   #     ##   ##  #
   #     # # # #  #        #
   #     #  #  #   #####   #
   #     #     #        #  #
   #     #     #        #  #
   #     #     #  #####    #

/**
 * @file ${lsl_stream_writer.py}
 * @brief Labstreaminglayer Writer
 *
 */


"""

from typing import Literal

import mne
import mne_lsl
import numpy as np

from ...TMSiSDK.device import ChannelType
from ...TMSiSDK.sample_data_server.sample_data_server import SampleDataServer
from ...TMSiSDK.tmsi_errors.error import (
    TMSiError,
    TMSiErrorCode,
)


class LSLConsumer:
    """
    Provides the .put() method expected by TMSiSDK.sample_data_server

    liblsl will handle the data buffer in a seperate thread. Since liblsl can
    bypass the global interpreter lock and python can't, and lsl uses faster
    compiled code, it's better to offload this than to create our own thread.
    """

    def __init__(self, lsl_outlet: mne_lsl.lsl.StreamOutlet):
        self._outlet = lsl_outlet

    def put(self, sd):
        """
        Pushes sample data to pylsl outlet, which handles the data buffer

        sd (TMSiSDK.sample_data.SampleData): provided by the sample data server
        """
        try:
            # reshape incoming samples
            signals = np.reshape(
                sd.samples,
                (sd.num_samples_per_sample_set, sd.num_sample_sets),
                order="F",
            )
            # and push to LSL
            self._outlet.push_chunk(signals, mne_lsl.lsl.local_clock())
        except:
            raise TMSiError(TMSiErrorCode.file_writer_error)


class LSLWriter:
    """
    A drop-in replacement for a TSMiSDK filewriter object
    that streams data to labstreaminglayer
    """

    def __init__(self, stream_name: str = "", chunk_size: int | Literal["auto"] = "auto"):
        self._name = stream_name if stream_name else "tmsi"
        self._chunk_size = chunk_size
        self._consumer = None
        self._outlet = None
        self._device_id = None

    def open(self, device):
        """
        Input is an open TMSiSDK device object
        """
        print("Opening TMSi MNE-LSL Writer.")
        self._device_id = device.get_id()
        try:
            sample_rate = device.get_device_sampling_frequency()
            num_channels = device.get_num_active_channels()

            if self._chunk_size == "auto":
                # Calculate nr of sample-sets within one sample-data-block:
                # This is the nr of sample-sets in 150 milli-seconds or when the
                # sample-data-block-size exceeds 64kb the it will become the nr of
                # sample-sets that fit in 64kb
                num_sample_sets_per_sample_data_block = int(sample_rate * 0.15)
                size_one_sample_set = num_channels * 4
                if (num_sample_sets_per_sample_data_block * size_one_sample_set) > 64000:
                    num_sample_sets_per_sample_data_block = int(64000 / size_one_sample_set)
                self._chunk_size = num_sample_sets_per_sample_data_block

            # provide LSL with metadata
            sinfo = mne_lsl.lsl.StreamInfo(
                name=self._name,
                stype="EEG",
                n_channels=num_channels,
                sfreq=sample_rate,
                dtype="float32",
                source_id=f"tmsi-{device.get_device_serial_number()}",
            )

            sinfo.set_channel_info()
            sinfo.set_channel_types()
            sinfo.set_channel_units()
            ch_names = []
            ch_units = []
            ch_types = []
            for ch in device.get_device_active_channels():
                ch_name = ch.get_channel_name()
                ch_type = ch.get_channel_type().value
                ch_names.append(ch_name)
                ch_units.append(ch.get_channel_unit_name())
                if (ch_type == ChannelType.UNI.value) and ch_name != "CREF":
                    ch_types.append_child_value("type", "EEG")
                elif ch_type == ChannelType.status.value:
                    ch_types.append_child_value("type", "STATUS")
                elif ch_type == ChannelType.counter.value:
                    ch_types.append_child_value("type", "COUNTER")
                else:
                    ch_types.append_child_value("type", "-")
            # sinfo.set_channel_names(ch_names)

            info = mne.create_info(
                ch_names=ch_names,
                sfreq=sample_rate,
                ch_types=["eeg"] * num_channels,  # set dummy types
                verbose=None,
            )
            info["device_info"] = {
                "type": "TMSi",
                "model:": device.get_device_type(),
                "serial": device.get_device_serial_number(),
                "site": "",
            }
            sinfo.set_channel_info(info)
            sinfo.set_channel_types(ch_types)
            sinfo.set_channel_units(ch_units)

            # start sampling data and pushing to LSL
            self._outlet = mne_lsl.lsl.StreamOutlet(sinfo=sinfo, chunk_size=self._chunk_size)
            self._consumer = LSLConsumer(self._outlet)
            SampleDataServer().register_consumer(self._device_id, self._consumer)

        except:
            raise TMSiError(TMSiErrorCode.file_writer_error)

    def close(self):
        print("Closing TMSi MNE-LSL Writer.")
        SampleDataServer().unregister_consumer(self._device_id, self._consumer)
        self._consumer = None
        self._outlet = None

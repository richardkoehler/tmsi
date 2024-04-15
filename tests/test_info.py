import mne
import mne_lsl


if __name__ == "__main__":
    sfreq = 4096
    ch_names = ["ecog", "eeg", "status", "counter"]
    ch_types = ["-", "EEG", "STATUS", "COUNTER"]
    ch_units = ["uV", "uV", "uV", "-"]
    # provide LSL with metadata
    sinfo = mne_lsl.lsl.StreamInfo(
        name="test",
        stype="EEG",
        n_channels=4,
        sfreq=sfreq,
        dtype="float32",
        source_id=f"tmsi-01",
    )

    info = mne.create_info(
        ch_names=ch_names,
        sfreq=sfreq,
        ch_types=["eeg"] * 4,
        verbose=None,
    )
    info["device_info"] = {
        "type": "TMSi",
        "model:": "SAGA",
        "serial": "1234",
        "site": "",
    }
    info.update({"temp": {"synchronization": {"offset_mean": "0.0335", "offset_std": "0.0008"}}})

    # The only entries that should be manually changed by the user are:
    # info['bads'], info['description'], info['device_info'] info['dev_head_t'],
    # info['experimenter'], info['helium_info'], info['line_freq'], info['temp'], and info['subject_info'].

    sinfo.set_channel_info(info)
    sinfo.set_channel_names(ch_names)
    sinfo.set_channel_types(ch_types)
    sinfo.set_channel_units(ch_units)
    print(sinfo.get_channel_info())
    print(sinfo.get_channel_types())
    print(sinfo.as_xml)
    # sinfo.set_channel_units()

    # # sinfo.set_channel_info(info)

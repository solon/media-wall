### Prerequisites

- A Raspberry Pi running [Raspbian Buster](https://www.raspberrypi.org/downloads/raspbian/)
- A [PaPiRus e-ink screen hat](https://uk.pi-supply.com/products/papirus-epaper-eink-screen-hat-for-raspberry-pi)

### Install dependencies

```
curl -sSL https://pisupp.ly/papiruscode | sudo bash
pip install python-frontmatter
pip install wget
```

### Clone from repository

```
cd ~
git clone https://github.com/solon/media-wall.git mediawall
```

### Start

```
cd mediawall
start.py
```

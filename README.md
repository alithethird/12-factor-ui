Flet app that helps you charm your app.





to run:

`cd flet`
`python3 -m venv venv`
`source venv/bin/activate`
`pip install -r requirements.txt`
`flet run`

to pack for Linux:

`flet pack main.py  --add-data "assets:assets" --name charm-gen`


sometimes packing fails with something similar to `libmpv.so.1 not found`

to fix it:

`sudo apt install libmpv-dev libmpv2`

`sudo ln -s /usr/lib/x86_64-linux-gnu/libmpv.so /usr/lib/libmpv.so.1`

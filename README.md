# slowloris.py - Simple slowloris in Python

## What is Slowloris?
Slowloris is basically an HTTP Denial of Service attack that affects threaded servers. It works like this:

1. We start making lots of HTTP requests.
2. We send headers periodically (every ~15 seconds) to keep the connections open.
3. We never close the connection unless the server does so. If the server closes a connection, we create a new one keep doing the same thing.

This exhausts the servers thread pool and the server can't reply to other people.

## Citation

If you found this work useful, please cite it as

```bibtex
@article{gkbrkslowloris,
  title = "Slowloris",
  author = "Gokberk Yaltirakli",
  journal = "github.com",
  year = "2015",
  url = "https://github.com/gkbrk/slowloris"
}
```

## How to install and run?
here's how you do it.

* `git clone https://github.com/gkbrk/slowloris.git`
* `cd slowloris`
* `python slowloris.py -ua --adaptive-sockets -s 4000 example.com`

## Configuration options
It is possible to modify the behaviour of slowloris with command-line
arguments. In order to get an up-to-date help document, just run
`slowloris -h`.

options:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  Port of webserver, usually 80
  -s SOCKETS, --sockets SOCKETS
                        Number of sockets to use in the test
  -v, --verbose         Increases logging
  -ua, --randuseragents
                        Randomizes user-agents with each request
  --https               Use HTTPS for the requests
  --sleeptime SLEEPTIME
                        Time to sleep between each header sent.
  --random-delay        Adds random delays to requests to evade rate limiting
  --adaptive-sockets    Adjust socket count based on response times

## License
The code is licensed under the GPL License.

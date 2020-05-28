import requests
from streamlink import Streamlink, NoPluginError, PluginError
import streamlink
import sys
import time
import random
from random import shuffle
from fake_useragent import UserAgent
import linecache

from threading import Thread

channel_url = ""
proxies_file = "Proxies_txt/good_proxy.txt"
processes = []
max_nb_of_threads = 1000

all_proxies = []
nb_of_proxies = 0

# Session creating for request
ua = UserAgent()
session = Streamlink()
session.set_option("http-headers", {'User-Agent': ua.random, "Client-ID": "ewvlchtxgqq88ru9gmfp1gmyt6h2b93"})


def print_exception():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))


def get_channel():
    # Reading the channel name - passed as an argument to this script
    if len(sys.argv) >= 2:
        global channel_url
        channel_url += sys.argv[1]
    else:
        print("An error has occurred while trying to read arguments. Did you specify the channel?")
        sys.exit(1)


def get_proxies():
    # Reading the list of proxies
    global nb_of_proxies
    try:
        lines = [line.rstrip("\n") for line in open(proxies_file)]
    except IOError as e:
        print("An error has occurred while trying to read the list of proxies: %s" % e.strerror)
        sys.exit(1)

    nb_of_proxies = len(lines)
    return lines


def get_url():
    # Other options are available such as 'best', 'audio_only'
    # Docks available https://streamlink.github.io/index.html
    quality = 'worst'

    # Attempt to fetch streams
    try:
        streams = session.streams(channel_url)
    except NoPluginError:
        exit("Streamlink is unable to handle the URL '{0}'".format(channel_url))
    except PluginError as err:
        exit("Plugin error: {0}".format(err))

    if not streams:
        exit("No streams found on URL '{0}'".format(channel_url))

    # Look for specified stream
    if quality not in streams:
        exit("Unable to find '{0}' stream on URL '{1}'".format(quality, channel_url))

    # We found the stream
    return streams[quality].url

def open_url(proxy_data, url):
    try:
        global all_proxies
        headers = {'User-Agent': ua.random}
        current_index = all_proxies.index(proxy_data)

        if proxy_data['url'] == "":
            proxy_data['url'] = url
        current_url = proxy_data['url']
        try:
             if time.time() - proxy_data['time'] >= random.randint(1, 5):
                current_proxy = {"http": proxy_data['proxy'], "https": proxy_data['proxy']}
                with requests.Session() as s:
                    response = s.head(current_url, proxies=current_proxy, headers=headers)
                print(f"Sent HEAD request with {current_proxy['http']} | {response.status_code} | {response.request} | {response}")
                proxy_data['time'] = time.time()
                all_proxies[current_index] = proxy_data
        except:
            # Most of times this will fail, because proxy is not responding
            print("************* Connection Error! *************")

    except (KeyboardInterrupt, SystemExit):
        sys.exit()


if __name__ == "__main__":
    # python threads_viewer.py channel_name
    if len(sys.argv) == 2:
        channel_url = "https://www.twitch.tv/" + sys.argv[1]

    elif len(sys.argv) == 3:
        # python threads_viewer.py channel_name 1000
        # sys.argv[0] is the file path
        # sys.argv[1] is the channel name "channel_name"
        # sys.argv[2] is the number of threads to use
        channel_url = "https://www.twitch.tv/" + sys.argv[1]
        max_nb_of_threads = int(sys.argv[2])
    
    else:
        print("Format must be: python threads_viewer.py channel_name 1000")
        sys.exit()

    print("Loading channel %s with %i threads." % (channel_url, max_nb_of_threads))
        
    start_time = time.time()
    proxies = get_proxies()
    
    for p in proxies:
        all_proxies.append({'proxy': p, 'time': time.time(), 'url': ""})

    shuffle(all_proxies)
    list_of_all_proxies = all_proxies
    current_proxy_index = 0

    while True:
        try:
            url = get_url()
        except: 
            print("We were unable to get a stream url for %s " % channel_url)
            sys.exit()
        try:
            for i in range(0, max_nb_of_threads):
                threaded = Thread(target=open_url, args=(all_proxies[random.randint(0, len(all_proxies))], url))
                threaded.daemon = True  # This thread dies when main thread (only non-daemon thread) exits.
                threaded.start()
        except:
            print_exception()
        shuffle(all_proxies)
        time.sleep(20)

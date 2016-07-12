#!/usr/bin/env python
########################
# Zabbix nsq monitoring script
#
# Supports:
#   - nsqd status
#   - nsqlookupd status
#   - nsq-to-file status
########################
# ChangeLog:
#  20160712  Sun Song <sunsongxp@gmail.com> initial creation
########################

# Usage example:
#
#
# `python nsq.py nsqd uptime`
# `python nsq.py nsqd health`
# `python nsq.py nsqd version`
#
# Discover the topics in this nsq server along with detailed information related to those topics.
# `python nsq.py nsqd discovery topics`
#
# List all nsqlookupd count in the while cluster
# `python nsq.py nsqlookupd count`
#
# List all nsqlookupd names in the whole cluster
# `python nsq.py nsqlookupd names`
#
# List all topics in the whole cluster
# `python nsq.py nsqlookupd topics`


import json
import os
import requests
import sys
import time

# Set conf default
conf = {
    u'nsq_host': u'127.0.0.1',
    u'nsq_nsqd': True,
    u'nsq_nsqd_http_port': 4151,
    u'nsq_nsqlookupd': True,
    u'nsq_nsqlookupd_http_port': 4161
}

conf_string = open(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "../conf/nsq.conf")
).read()


# Load confi from nsq.conf and replace the default ones
conf.update(json.loads(conf_string))

# Generate config that can be obtained from the existing ones.
conf.update({
    "nsq_nsqd_url": "http://%s:%s" % (
        conf["nsq_host"],
        conf["nsq_nsqd_http_port"],
    ),
    "nsq_nsqlookupd_url": "http://%s:%s" % (
        conf["nsq_host"],
        conf["nsq_nsqlookupd_http_port"]
    ),
})


def handle_nsqd(key, extra_keys=[]):
    """
    Get info from nsqd
    """
    nsqd = NSQd()
    if key == "uptime":
        print nsqd.uptime

    elif key == "health":
        print nsqd.health

    elif key == "version":
        print nsqd.version

    elif key == "discovery":
        discovery_item = extra_keys[0]
        if discovery_item == "topics":
            topics = nsqd.topics
            data = []
            for topic in topics:
                data.append({
                    "{#TOPICNAME}": topic['topic_name'],
                    "{#BACKENDDEPTH}": topic['backend_depth'],
                    "{#DEPTH}": topic['depth'],
                    "{#MESSAGE_COUNT}": topic['message_count'],
                    "{#PAUSED}": topic['paused'],
                })
            print json.dumps({"data": data})


def handle_nsqlookupd(key):
    """
    Get info from nsqlookupd
    """
    nsqlookupd = NSQLookupd()
    if key == "count":
        print len(nsqlookupd.node_names)

    elif key == "names":
        print ", ".join(nsqlookupd.node_names)

    elif key == "topics":
        print ", ".join(nsqlookupd.topic_names)


class NSQd():
    def __init__(self):
        self.base_url = conf.get("nsq_nsqd_url")
        self.info_url = "%s/info" % self.base_url
        self.stat_url = "%s/stats" % self.base_url

    def get_info(self):
        """
        Get basic info for this NSQD
        """
        return requests.get(self.info_url).json().get("data")

    def get_stat(self, topic=None):
        """
        Get stats for either a specific topic or all topics in this NSQD.
        If the topic is None, then all topics stats will be retrieved.
        """
        params = {
            "format": "json",
        }
        if topic:
            params["topic"] = topic

        return requests.get(self.stat_url, params=params).json().get("data")

    @property
    def uptime(self):
        start_time = self.get_info().get("start_time")
        return int(time.time() - start_time)

    @property
    def version(self):
        return self.get_info().get("version")

    @property
    def health(self):
        return self.get_stat().get("health")

    @property
    def topics(self):
        topics_info = self.get_stat().get("topics")
        return [{
            "topic_name": topic_info.get("topic_name"),
            "backend_depth": topic_info.get("backend_depth"),
            "depth": topic_info.get("depth"),
            "paused": topic_info.get("paused"),
            "message_count": topic_info.get("message_count"),
        } for topic_info in topics_info]


class NSQLookupd():
    def __init__(self):
        self.base_url = conf.get("nsq_nsqlookupd_url")
        self.all_nodes_url = "%s/nodes" % self.base_url
        self.all_topics_url = "%s/topics" % self.base_url

    def get_nodes_info(self):
        """
        Get all NSQD nodes registered in this NSQLookupd.
        """
        return requests.get(self.all_nodes_url).json().get("data")

    def get_topics_info(self):
        """
        Get all topics in this cluster. (Each NSQLookupd have all topics info)
        """
        return requests.get(self.all_topics_url).json().get("data")

    @property
    def node_names(self):
        node_names = []
        nodes_info = self.get_nodes_info()
        if nodes_info:
            nodes = nodes_info.get("producers")
            for node in nodes:
                node_names.append(node["hostname"])

        if node_names:
            node_names.sort()

        return node_names

    @property
    def topic_names(self):
        topics_info = self.get_topics_info()
        topic_names = topics_info.get("topics")

        if topic_names:
            topic_names.sort()

        return topic_names


def main():
    args = sys.argv[1:]

    if len(args) < 1:
        raise Exception("Argument not provided.")

    service = args[0]
    key = args[1]

    if len(args) > 2:
        extra_keys = args[2:]
    else:
        extra_keys = []

    if service == "nsqd":
        handle_nsqd(key, extra_keys)

    elif service == "nsqlookupd":
        handle_nsqlookupd(key)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
########################
# Zabbix couchbase monitoring script
#
# Supports:
#  - nodes, bucket names discovery
#  - cluster items
#  - bucket itmes
#  - node items
########################
# ChangeLog:
#  20160425  Sun Song <sunsongxp@gmail.com> initial creation
########################
# Usage examples:

# Discovery
# python couchbase.py discovery buckets string_list
# python couchbase.py discovery nodes string_list

# Cluster:

# python couchbase.py cluster maxBucketCount int
# python couchbase.py cluster name string
# python couchbase.py cluster buckets.uri string
# python couchbase.py cluster storageTotals.hdd.free int
# python couchbase.py cluster nodes string_list

# Bucket

# python couchbase.py bucket <name>  stats.op.samples.ops avg

# Node
# python couchbase.py node <hostname> interestingStats.couch_views_data_size int

########################

import json
import requests
import sys
import urlparse


# Load configuration file
conf_string = open("../conf/couchbase.conf").read()
conf_json = json.loads(conf_string)

couchbase_api_endpoint = conf_json.get("api_endpoint")

if not couchbase_api_endpoint:
    raise Exception("api_endpoint is not provided in configuration file")

cluster_url = urlparse.urljoin(couchbase_api_endpoint, "/pools/default/")
buckets_url = urlparse.urljoin(couchbase_api_endpoint, "/pools/default/buckets/")


def get_from_url(url, params={}):
    return json.loads(requests.get(url, params=params).content)

def handle_data_by_type(value, data_type, macro=None):
    if data_type == "int":
        return int(value)

    if data_type == "string":
        return str(value)

    # if data_type is avg, then value should be a list,
    # and the each element in this list is numeric.
    # then take average of values in this list.
    if data_type == "avg":
        assert type(value) == list
        return sum(value) / float(len(value))

    # value should be a list of string
    if data_type == "string_list":
        assert type(value) == list
        return json.dumps({
            "data": [{"%s%s%s" % ("{", macro, "}") : str(item)} for item in value]
        })

def get_data_from_keys(data, keys_string):
    """
    Get wanted data through layers.
    """
    keys = keys_string.split(".")
    for key in keys:
        data = data[key]
    return data


def handle_cluster(args):
    # couchbase['cluster', key, type]
    data = get_from_url(cluster_url)
    data_type = args[1]
    keys_string = args[0]

    result = get_data_from_keys(data, keys_string)

    print handle_data_by_type(result, data_type)


def handle_bucket(args):

    # couchbase['bucket', name, key, type]
    name = args[0]
    data_type = args[2]

    bucket_url = urlparse.urljoin(buckets_url, "%s/" % name)

    # couchbase['bucket', name, 'stats.*', type]
    keys_string = args[1]
    if keys_string.startswith("stats"):
        bucket_stats_url = urlparse.urljoin(bucket_url, "stats?zoom=minute")
        data = get_from_url(bucket_stats_url)
        result = get_data_from_keys(data, keys_string.split(".", 1)[1])
    else:
        data = get_from_url(bucket_url)
        # couchbase['bucket', name, "nodes.hostnames", "string"]
        if keys_string == "nodes.hostnames":
            result = [node['hostname'] for node in get_data_from_keys(data, "nodes")]
            result = ", ".join(result)
        # couchbase['bucket', name, "*", type]
        else:
            result = get_data_from_keys(data, keys_string)

    print handle_data_by_type(result, data_type)


def handle_node(args):
    # couchbase['node', hostname, key, type]
    hostname = args[0]
    nodes = get_from_url(cluster_url).get("nodes")
    data_type = args[2]
    for node in nodes:
        if node.get("hostname").split(":")[0] == hostname:
            data = node
            break
    result = get_data_from_keys(data, args[1])

    print handle_data_by_type(result, data_type)


def handle_discovery(args):
    # couchbase['discovery', key, type]
    data_type = args[1]
    keys_string = args[0]

    if keys_string == "nodes":
        data = get_from_url(cluster_url)
        result = get_data_from_keys(data, keys_string)
        nodes = [item['hostname'].split(":")[0] for item in result]
        print handle_data_by_type(nodes, data_type, "#NODEHOST")
        return

    if keys_string == "buckets":
        # couchbase['discovery', 'buckets', type]
        # type here is `string_list`
        data = get_from_url(buckets_url)
        bucket_names = [bucket['name'] for bucket in data]
        print handle_data_by_type(bucket_names, args[1], "#BUCKETNAME")
        return


def main():
    args = sys.argv[1:]

    if len(args) < 1:
        raise Exception("Argument not provided.")

    # The object_type (first agrument) is either cluster, bucket, or node.
    object_type = args[0]
    extra_args = [arg for arg in args[1:] if arg != ""]

    if object_type == "cluster":
        handle_cluster(extra_args)

    elif object_type == "bucket":
        handle_bucket(extra_args)

    elif object_type == "node":
        handle_node(extra_args)

    elif object_type == "discovery":
        handle_discovery(extra_args)
    else:
        raise Exception("Argument is not either cluster, bucket, node")


if __name__ == "__main__":
    main()

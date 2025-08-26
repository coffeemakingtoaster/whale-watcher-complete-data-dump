import json
import os
from typing import List
import re


RULES = ["curlUseFlagF",
     "npmCacheCleanAfterInstall",
     "npmCacheCleanUseForce",
     "rmRecursiveAfterMktempD",
     "curlUseHttpsUrl",
     "wgetUseHttpsUrl",
     "pipUseNoCacheDir",
     "mkdirUsrSrcThenRemove",
     "configureShouldUseBuildFlag",
     "gemUpdateSystemRmRootGem",
     "sha256sumEchoOneSpaces",
     "gemUpdateNoDocument",
     "gpgVerifyAscRmAsc",
     "yumInstallForceYes",
     "yumInstallRmVarCacheYum",
     "tarSomethingRmTheSomething",
     "gpgUseBatchFlag",
     "gpgUseHaPools",
     "ruleAptGetInstallUseY",
     "ruleAptGetUpdatePrecedesInstall",
     "ruleAptGetInstallUseNoRec",
     "ruleAptGetInstallThenRemoveAptLists",
     "apkAddUseNoCache"
]



def __parse_out_file(filename: str) -> List:
    with open(filename) as f:
        data = f.readlines()
    rules = []

    pattern = re.compile(r'(?:\x1B\[[0-?]*[ -/]*[@-~])*ruleId=(?:\x1B\[[0-?]*[ -/]*[@-~])*(\S+)')

    for line in data:
        match = re.search(pattern, line)
        if match:
            print("rule")
            rule_id = match.group(1)
            print(rule_id)
            rules.append(rule_id)

    return rules

def parse_hits():

    rule_hits = {}
    for rule in RULES:
        rule_hits[rule] = {"whalewatcher": -1, "binnacle": -1}

    # parse binnacle
    with open("./out/results-gold-summary.txt") as f:
        data = json.load(f)
        for key in data.keys():
            rule_hits[key]['binnacle'] = data[key]['violations']

    directory = os.fsencode("./ww_out/")
    
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".out"):
            rules = __parse_out_file(os.path.join("./ww_out/", filename))
            for rule in rules:
                if rule in rule_hits:
                    rule_hits[rule]['whalewatcher'] = max(rule_hits[rule]['whalewatcher'],0) + 1

    return rule_hits

def print_rule_hits(rule_hits):
    max_rule_length = 0
    for rule in RULES:
        max_rule_length = max(max_rule_length, len(rule))

    print("whalewatcher\tbinnacle")
    for key in rule_hits.keys():
        r = rule_hits[key]
        print("-"*10)
        print(f"|{key}{' '*(max_rule_length - len(key))}|{r['whalewatcher']}|\t{r['binnacle']}|")
    print("-"*10)


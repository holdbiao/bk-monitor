#!/bin/bash

share_path=${BK_HOME:-/data/bkee}/public/paas_agent/share

mkdir -p ${share_path}/bk_monitorv3
/bin/cp -rf ${share_path}/bk_monitor/* ${share_path}/bk_monitorv3

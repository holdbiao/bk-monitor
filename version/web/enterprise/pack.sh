#!/bin/bash

# params:
# $1: PROJECT_DIR

cd "$BASEDIR" || exit
CURRENT_DIR=$(pwd)

# 0. Check source code dir
PROJECT_DIR=$1
if [ ! -e "${PROJECT_DIR}" ]
then
    echo "DIR ${PROJECT_DIR} not exit!"
    exit 1
fi

# 1. Create tmp dir
[ -e "${CURRENT_DIR}"/tmp/ ] && rm -rf "${CURRENT_DIR}"/tmp/
mkdir -p "${CURRENT_DIR}"/tmp/

# 2. Copy enterprise files
## 2.1 copy config
mkdir -p "${CURRENT_DIR}"/tmp/conf/platform
mkdir -p "${CURRENT_DIR}"/tmp/conf/web/development
mkdir -p "${CURRENT_DIR}"/tmp/conf/web/production
mkdir -p "${CURRENT_DIR}"/tmp/conf/web/testing
cp -R ${PROJECT_DIR}/conf/__init__.py "${CURRENT_DIR}"/tmp/conf/__init__.py
cp -R ${PROJECT_DIR}/conf/default_settings.py "${CURRENT_DIR}"/tmp/conf/default_settings.py
cp -R ${PROJECT_DIR}/conf/platform/__init__.py "${CURRENT_DIR}"/tmp/conf/platform/__init__.py
cp -R ${PROJECT_DIR}/conf/platform/default_settings.py "${CURRENT_DIR}"/tmp/conf/platform/default_settings.py
cp -R ${PROJECT_DIR}/conf/platform/enterprise.py "${CURRENT_DIR}"/tmp/conf/platform/enterprise.py
cp -R ${PROJECT_DIR}/conf/web/__init__.py "${CURRENT_DIR}"/tmp/conf/web/__init__.py
cp -R ${PROJECT_DIR}/conf/web/sentry.py "${CURRENT_DIR}"/tmp/conf/web/sentry.py
cp -R ${PROJECT_DIR}/conf/web/default_settings.py "${CURRENT_DIR}"/tmp/conf/web/default_settings.py
cp -R ${PROJECT_DIR}/conf/web/development/__init__.py "${CURRENT_DIR}"/tmp/conf/web/development/__init__.py
cp -R ${PROJECT_DIR}/conf/web/development/default_settings.py "${CURRENT_DIR}"/tmp/conf/web/development/default_settings.py
cp -R ${PROJECT_DIR}/conf/web/development/enterprise.py "${CURRENT_DIR}"/tmp/conf/web/development/enterprise.py
cp -R ${PROJECT_DIR}/conf/web/production/__init__.py "${CURRENT_DIR}"/tmp/conf/web/production/__init__.py
cp -R ${PROJECT_DIR}/conf/web/production/default_settings.py "${CURRENT_DIR}"/tmp/conf/web/production/default_settings.py
cp -R ${PROJECT_DIR}/conf/web/production/enterprise.py "${CURRENT_DIR}"/tmp/conf/web/production/enterprise.py
cp -R ${PROJECT_DIR}/conf/web/testing/__init__.py "${CURRENT_DIR}"/tmp/conf/web/testing/__init__.py
cp -R ${PROJECT_DIR}/conf/web/testing/default_settings.py "${CURRENT_DIR}"/tmp/conf/web/testing/default_settings.py
cp -R ${PROJECT_DIR}/conf/web/testing/enterprise.py "${CURRENT_DIR}"/tmp/conf/web/testing/enterprise.py

## 2.2 copy static
cp -R ${PROJECT_DIR}/static "${CURRENT_DIR}"/tmp
cp ${PROJECT_DIR}/bk_monitorv3.png "${CURRENT_DIR}"/tmp/bk_monitorv3.png

## 2.3 copy templates
cp -R ${PROJECT_DIR}/templates "${CURRENT_DIR}"/tmp

## 2.4 copy locale i18n path
cp -R ${PROJECT_DIR}/locale "${CURRENT_DIR}"/tmp

## 2.5 copy python
cp -R ${PROJECT_DIR}/iam "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/bk_dataview "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/bkmonitor "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/metadata "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/packages "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/patches "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/api "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/core "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/constants "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/monkey.py "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/urls.py "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/manage.py "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/settings.py "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/wsgi.py "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/requirements.txt "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/version/web/enterprise/app.yml "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/version/web/enterprise/release.md "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/version_logs_md/ "${CURRENT_DIR}"/tmp
#cp -R ${PROJECT_DIR}/blueapps "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/blueking "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/config "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/runtime.txt "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/ignorefile "${CURRENT_DIR}"/tmp

mkdir -p "${CURRENT_DIR}"/tmp/support-files/iam/
cp -R ${PROJECT_DIR}/support-files/iam/* "${CURRENT_DIR}"/tmp/support-files/iam/

ls -alh "${CURRENT_DIR}"/tmp/



# 3. Clean
## 3.1 replace variable
sed -i '/# internal/d' "${CURRENT_DIR}"/tmp/requirements.txt
sed -i '/# backend/d' "${CURRENT_DIR}"/tmp/requirements.txt
sed -i 's/#.*//g' "${CURRENT_DIR}"/tmp/requirements.txt
sed -i '/BKAPP_DEPLOY_PLATFORM/s/ieod/enterprise/g' "${CURRENT_DIR}"/tmp/settings.py
sed -i '/_choices/s/\[.*\]/\["enterprise",\]/g' "${CURRENT_DIR}"/tmp/settings.py
sed -i 's/BKAPP_DEPLOY_PLATFORM =.*/BKAPP_DEPLOY_PLATFORM = "enterprise"/g' "${CURRENT_DIR}"/tmp/settings.py
sed -i '/BKAPP_DEPLOY_PLATFORM/s/ieod/enterprise/g' "${CURRENT_DIR}"/tmp/conf/platform/default_settings.py
#sed -i '/ieod\|tencent\|qcloud\|bkclouds\|community/d' "${CURRENT_DIR}"/tmp/conf/platform/default_settings.py
sed -i 's/"ieod"/"enterprise"/g' "${CURRENT_DIR}"/tmp/conf/web/default_settings.py
sed -i 's/te =.*/te = False/g' "${CURRENT_DIR}"/tmp/packages/common/context_processors.py
sed -i 's/me =.*/me = False/g' "${CURRENT_DIR}"/tmp/packages/common/context_processors.py
sed -i 's/ee =.*/ee = True/g' "${CURRENT_DIR}"/tmp/packages/common/context_processors.py
sed -i 's/ce =.*/ce = False/g' "${CURRENT_DIR}"/tmp/packages/common/context_processors.py

# 3.2 clean dir&file
rm -rf "${CURRENT_DIR}"/tmp/packages/monitor/resource/bkclouds
rm -rf "${CURRENT_DIR}"/tmp/packages/monitor/resource/tencent
rm -rf "${CURRENT_DIR}"/tmp/packages/monitor/resource/community
rm -rf "${CURRENT_DIR}"/tmp/packages/monitor/resource/ieod

rm -rf "${CURRENT_DIR}"/tmp/packages/account/components/bk_ticket
rm -rf "${CURRENT_DIR}"/tmp/packages/account/components/ptlogin
rm -rf "${CURRENT_DIR}"/tmp/packages/account/components/qcloud_ptlogin
rm -rf "${CURRENT_DIR}"/tmp/packages/account/sites/ieod
rm -rf "${CURRENT_DIR}"/tmp/packages/account/sites/clouds
rm -rf "${CURRENT_DIR}"/tmp/packages/account/sites/qcloud
rm -rf "${CURRENT_DIR}"/tmp/packages/account/sites/community
rm -rf "${CURRENT_DIR}"/tmp/packages/monitor/resource/config.pyi
find "${CURRENT_DIR}"/tmp/packages/healthz/healthz_test/ -type f -a ! -name '*init*' -a ! -name '*enterprise*' -delete

rm -rf "${CURRENT_DIR}"/tmp/templates/weixin
rm -rf "${CURRENT_DIR}"/tmp/templates/adapter/bkclouds
rm -rf "${CURRENT_DIR}"/tmp/templates/adapter/tencent
rm -rf "${CURRENT_DIR}"/tmp/templates/adapter/community
rm -rf "${CURRENT_DIR}"/tmp/templates/adapter/ieod

rm -rf "${CURRENT_DIR}"/tmp/locale/worker

rm -rf "${CURRENT_DIR}"/tmp/static/weixin
rm -rf "${CURRENT_DIR}"/tmp/static/guide
rm -rf "${CURRENT_DIR}"/tmp/package-lock.json

rm -rf "${CURRENT_DIR}"/tmp/api/*/ieod
rm -rf "${CURRENT_DIR}"/tmp/api/*/community

rm -rf "${CURRENT_DIR}"/tmp/version

rm -rf "${CURRENT_DIR}"/tmp/bkmonitor/utils/rsa/bk.key

rm -rf "${CURRENT_DIR}"/tmp/Aptfile

# 4. Replace the original project directory
[ -e "${PROJECT_DIR}" ] && rm -rf "${PROJECT_DIR}"
mkdir -p "${CURRENT_DIR}/${PROJECT_DIR}"
mv "${CURRENT_DIR}"/tmp/* "${PROJECT_DIR}"/

rm -rf "${CURRENT_DIR}"/tmp
ls -alh "${PROJECT_DIR}"/

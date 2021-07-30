#!/bin/bash

# params:
# $1: PROJECT_DIR
# $2: RELEASE_ENV [ce|ee]

cd "$BASEDIR" || exit
CURRENT_DIR=$(pwd)

# 0. Check script params
PROJECT_DIR=$1
if [ ! -e "${PROJECT_DIR}" ]
then
    echo "DIR ${PROJECT_DIR} not exit!"
    exit 1
fi

RELEASE_ENV=$2
case ${RELEASE_ENV} in
    ce)
        PLATFORM="community"
        ;;
    ee)
        PLATFORM="enterprise"
        ;;
    *)
        echo "RELEASE_ENV not set, check your config"
        exit 1
        ;;
esac

# 1. Create tmp dir
[ -e "${CURRENT_DIR}"/tmp/ ] && sudo rm -rf "${CURRENT_DIR}"/tmp/
mkdir -p "${CURRENT_DIR}"/tmp/

# 2. Copy files
## 2.1 Copy conf
mkdir -p "${CURRENT_DIR}"/tmp/conf/worker/production

# 重命名并清理文件
mv ${PROJECT_DIR}/conf/api/production/community_gunicorn_config.py ${PROJECT_DIR}/conf/api/production/gunicorn_config.py
rm ${PROJECT_DIR}/conf/api/production/enterprise.py
rm ${PROJECT_DIR}/conf/api/production/enterprise_gunicorn_config.py

cp -R ${PROJECT_DIR}/conf "${CURRENT_DIR}"/tmp
find "${CURRENT_DIR}"/tmp/conf -name '*.py' -a ! -name '*init*' -a ! -name '*default_settings*' -a ! -name '*'${PLATFORM}'*' -a ! -name '*gunicorn_config*' -delete
cp -R ${PROJECT_DIR}/conf/web/sentry.py "${CURRENT_DIR}"/tmp/conf/web/sentry.py

## 2.2 Copy src dir
cp -R ${PROJECT_DIR}/bin "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/patches "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/alarm_backends "${CURRENT_DIR}"/tmp

cp -R ${PROJECT_DIR}/kernel_api "${CURRENT_DIR}"/tmp
cp ${PROJECT_DIR}/docs/api/monitor_v3.yaml "${CURRENT_DIR}"/tmp/kernel_api
cp -R ${PROJECT_DIR}/wsgi.py "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/gunicorn_config.py "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/templates "${CURRENT_DIR}"/tmp

cp -R ${PROJECT_DIR}/packages "${CURRENT_DIR}"/tmp
# find "${CURRENT_DIR}"/tmp/packages -size +500k -a -not -name '*.py' | grep -E 'exporter|tar.gz|exe|linux|windows' | xargs rm -f || true

cp -R ${PROJECT_DIR}/blueking "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/config "${CURRENT_DIR}"/tmp

cp ${PROJECT_DIR}/on_migrate "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/iam "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/bk_dataview "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/bkmonitor "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/metadata "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/query_api "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/api "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/core "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/constants "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/monkey.py "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/settings.py "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/manage.py "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/requirements.txt "${CURRENT_DIR}"/tmp
if [ "${PLATFORM}" == "enterprise" ]; then
    cp -R ${PROJECT_DIR}/locale "${CURRENT_DIR}"/tmp
fi

## 2.3 Copy version file
cp -R ${PROJECT_DIR}/version/worker/${PLATFORM}/VERSION "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/version/worker/${PLATFORM}/release.md "${CURRENT_DIR}"/tmp
cp -R ${PROJECT_DIR}/version/worker/${PLATFORM}/project.yml "${CURRENT_DIR}"/tmp

## 2.4 Copy support-files
if [ -d ${PROJECT_DIR}/support-files/templates/container_community ]
then
  rm -r ${PROJECT_DIR}/support-files/templates/container_community
fi

cp -R ${PROJECT_DIR}/support-files "${CURRENT_DIR}"


# 3. Clean file

rm -rf "${CURRENT_DIR}"/tmp/packages/account/components/bk_ticket
rm -rf "${CURRENT_DIR}"/tmp/packages/account/components/ptlogin
rm -rf "${CURRENT_DIR}"/tmp/packages/account/components/qcloud_ptlogin
rm -rf "${CURRENT_DIR}"/tmp/packages/account/sites/ieod
rm -rf "${CURRENT_DIR}"/tmp/packages/account/sites/clouds
rm -rf "${CURRENT_DIR}"/tmp/packages/account/sites/qcloud
rm -rf "${CURRENT_DIR}"/tmp/packages/account/sites/enterprise
rm -rf "${CURRENT_DIR}"/tmp/packages/weixin
rm -rf "${CURRENT_DIR}"/tmp/packages/monitor/resource/config.pyi
find "${CURRENT_DIR}"/tmp/packages/healthz/healthz_test/ -type f -a ! -name '*init*' -a ! -name '*'${PLATFORM}'*' -delete

rm -rf "${CURRENT_DIR}"/tmp/api/*/enterprise/
rm -rf "${CURRENT_DIR}"/tmp/api/*/ieod/

rm -rf "${CURRENT_DIR}"/tmp/templates/weixin
rm -rf "${CURRENT_DIR}"/tmp/templates/adapter/enterprise
rm -rf "${CURRENT_DIR}"/tmp/templates/adapter/ieod

rm -rf "${CURRENT_DIR}"/tmp/locale/web
sed -i "/BKAPP_DEPLOY_PLATFORM/s/ieod/${PLATFORM}/g" "${CURRENT_DIR}"/tmp/settings.py
sed -i "/_choices/s/\[.*\]/\[\"${PLATFORM}\"\]/g" "${CURRENT_DIR}"/tmp/settings.py
sed -i '/BKAPP_DEPLOY_PLATFORM/s/ieod/community/g' "${CURRENT_DIR}"/tmp/conf/platform/default_settings.py
sed -i 's/"ieod"/"community"/g' "${CURRENT_DIR}"/tmp/conf/web/default_settings.py

find "${CURRENT_DIR}"/tmp -name '*.py' -exec python "${CURRENT_DIR}"/tmp/bkmonitor/utils/code_clean.py {} -w -b "&PACK" -n "${RELEASE_ENV}" \;

cp "${CURRENT_DIR}"/support-files/sql/${PLATFORM}/* "${CURRENT_DIR}"/support-files/sql/
rm -rf "${CURRENT_DIR}"/support-files/sql/enterprise
rm -rf "${CURRENT_DIR}"/support-files/sql/community
rm -rf "${CURRENT_DIR}"/support-files/sql/ieod
cp "${CURRENT_DIR}"/support-files/templates/${PLATFORM}/* "${CURRENT_DIR}"/support-files/templates/
rm -rf "${CURRENT_DIR}"/support-files/templates/enterprise
rm -rf "${CURRENT_DIR}"/support-files/templates/community
rm -rf "${CURRENT_DIR}"/support-files/templates/ieod
rm -rf "${CURRENT_DIR}"/support-files/pkgs/bkoauth-0.0.21.tar.gz

rm -rf "${CURRENT_DIR}"/tmp/bkmonitor/utils/rsa/bk.key
rm -rf "${CURRENT_DIR}"/tmp/Aptfile

# 4. requirements.txt into two file
sed -i '/# internal/d' "${CURRENT_DIR}"/tmp/requirements.txt
sed -i '/# ieod requirment/d' "${CURRENT_DIR}"/tmp/requirements.txt
sed -i '/^#/d' "${CURRENT_DIR}"/tmp/requirements.txt
grep "self-developed"  "${CURRENT_DIR}"/tmp/requirements.txt >  "${CURRENT_DIR}"/tmp/02_requirements_local.txt
grep -v "self-developed"  "${CURRENT_DIR}"/tmp/requirements.txt >  "${CURRENT_DIR}"/tmp/01_requirements.txt


# 5. Replace the original project directory
[ -e "${PROJECT_DIR}" ] && rm -rf "${PROJECT_DIR}"
mkdir -p "${CURRENT_DIR}/${PROJECT_DIR}"
mv "${CURRENT_DIR}"/tmp/* "${PROJECT_DIR}"/

touch "${PROJECT_DIR}"/SELF_CONTAINED_PIP_PKG
rm -rf "${CURRENT_DIR}"/tmp
ls -alh "${PROJECT_DIR}"/

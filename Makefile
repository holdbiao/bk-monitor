MAKE_FILE_DIR = $(shell pwd)/$(lastword $(MAKEFILE_LIST))
PROJECT_DIR = $(shell dirname $(MAKE_FILE_DIR))

TENCENT_ENV := DJANGO_CONF_MODULE=conf.worker.development.tencent BKAPP_DEPLOY_PLATFORM=tencent
BKCLOUDS_ENV := DJANGO_CONF_MODULE=conf.worker.development.bkclouds BKAPP_DEPLOY_PLATFORM=bkclouds
TENCENT_WEB_ENV := DJANGO_CONF_MODULE=conf.web.development.tencent BKAPP_DEPLOY_PLATFORM=tencent
ENTERPRISE_WEB_ENV := DJANGO_CONF_MODULE=conf.web.development.enterprise BKAPP_DEPLOY_PLATFORM=enterprise
TENCENT_API_ENV := DJANGO_CONF_MODULE=conf.api.development.tencent BKAPP_DEPLOY_PLATFORM=tencent
EE_API_ENV := DJANGO_CONF_MODULE=conf.api.development.enterprise BKAPP_DEPLOY_PLATFORM=enterprise
BKCLOUDS_API_ENV := DJANGO_CONF_MODULE=conf.api.development.bkclouds BKAPP_DEPLOY_PLATFORM=bkclouds
MANAGEPY := ${PROJECT_DIR}/manage.py
PYTHONENV := PYTHONPATH=${PROJECT_DIR}
PYTHON_BIN := $(or ${PYTHON_BIN}, )
PYTHON := ${PYTHON_BIN}python
PIP := ${PYTHON_BIN}pip
FLAKE8 := ${PYTHON_BIN}flake8
PYLINT := ${PYTHON_BIN}pylint

DOMAIN = messages
LOCALE_DIR = $(PROJECT_DIR)/locale
BABEL_CONFIG_FILE = $(LOCALE_DIR)/babel.cfg
DJANGO_POT_FILE = $(LOCALE_DIR)/messages.pot

SAAS_LOCALE_DIR = $(PROJECT_DIR)/locale
SAAS_BABEL_CONFIG_FILE = $(SAAS_LOCALE_DIR)/babel.cfg
SAAS_BABEL_CONFIG_JS_FILE = $(SAAS_LOCALE_DIR)/babeljs.cfg
SAAS_DJANGO_POT_FILE = $(SAAS_LOCALE_DIR)/django.pot
SAAS_DJANGO_POT_JS_FILE = $(SAAS_LOCALE_DIR)/djangojs.pot

WEBPACK_DIR = $(PROJECT_DIR)/webpack

.PHONY : saas-i18n saas-i18n-python saas-i18n-js saas-i18n-update saas-i18n-updatejs saas-i18n-compile

help:
	@echo ""
	@echo "    Make sure that pybabel, gettext is installed"
	@echo ""
	@echo "    saas-i18n               - extract -> update -> compile (all)"
	@echo "    saas-i18n-python        - extract -> update -> compile (python & html)"
	@echo "    saas-i18n-js            - extract -> update -> compile (js)"
	@echo "    saas-i18n-update        - extract -> update (all)"
	@echo "    saas-i18n-updatepython  - extract -> update (python & html)"
	@echo "    saas-i18n-updatejs      - extract -> update (js)"
	@echo "    saas-i18n-compile       - compile (all)"
	@echo ""

saas-i18n: saas-i18n-python saas-i18n-js

saas-i18n-compile:
	cd $(PROJECT_DIR) && pybabel compile -D django -d $(SAAS_LOCALE_DIR)
	cd $(PROJECT_DIR) && pybabel compile -D djangojs -d $(SAAS_LOCALE_DIR)

saas-i18n-updatepython:
	cd $(PROJECT_DIR) && pybabel extract -k _ -k _lazy --no-location -F $(SAAS_BABEL_CONFIG_FILE) -o $(SAAS_DJANGO_POT_FILE) .
	cd $(PROJECT_DIR) && pybabel update -l en -d $(SAAS_LOCALE_DIR) -D django -i $(SAAS_DJANGO_POT_FILE)
	cd $(PROJECT_DIR) && pybabel update -l zh_Hans -d $(SAAS_LOCALE_DIR) -D django -i $(SAAS_DJANGO_POT_FILE)

saas-i18n-updatejs:
	cd $(PROJECT_DIR) && pybabel extract --no-location -F $(SAAS_BABEL_CONFIG_JS_FILE) -o $(SAAS_DJANGO_POT_JS_FILE) .
	cd $(PROJECT_DIR) && pybabel update -l en -d $(SAAS_LOCALE_DIR) -D djangojs -i $(SAAS_DJANGO_POT_JS_FILE)
	cd $(PROJECT_DIR) && pybabel update -l zh_Hans -d $(SAAS_LOCALE_DIR) -D djangojs -i $(SAAS_DJANGO_POT_JS_FILE)

saas-i18n-update: saas-i18n-updatepython  saas-i18n-updatejs

saas-i18n-js: saas-i18n-updatejs saas-i18n-compile

saas-i18n-python: saas-i18n-updatepython saas-i18n-compile

.PHONY: test
test:
	${PYTHON} ${MANAGEPY} test -v 1

.PHONY: test-saas
test-saas:
	${PYTHON} ${MANAGEPY} test -v 1 bkmonitor monitor monitor_api

.PHONY: test-backend
test-backend:
	${PYTHON} ${MANAGEPY} run_test -v 1 bkmonitor kernel project

.PHONY: create-error-document
create-error-document:
	${PYTHON} ${MANAGEPY} create_error_document -o bkmonitor/errors/README.md

.PHONY: lint
lint:
	${FLAKE8} --config=.flake8

.PHONY: full-lint
full-lint:
	${PYLINT} --rcfile=.pylint.conf `find -name '__init__.py' -maxdepth 2 -exec dirname {} \;`

.PHONY: runserver-tencent-worker
runserver-tencent-worker:
	env ${TENCENT_API_ENV} BKAPP_DEPLOY_ENV=api ${PYTHON} ${MANAGEPY} runserver 0:8000

.PHONY: runserver-enterprise-worker
runserver-enterprise-worker:
	env ${EE_API_ENV} BKAPP_DEPLOY_ENV=api ${PYTHON} ${MANAGEPY} runserver 0:8000

.PHONY: shell-tencent-worker
shell-tencent-worker:
	env ${TENCENT_API_ENV} BKAPP_DEPLOY_ENV=worker ${PYTHON} ${MANAGEPY} shell

.PHONY: runserver-bkclouds-worker
runserver-bkclouds-worker:
	env ${BKCLOUDS_API_ENV} BKAPP_DEPLOY_ENV=worker ${PYTHON} ${MANAGEPY} runserver 0:8000

.PHONY: runserver-tencent-web
runserver-tencent-web:
	env ${TENCENT_WEB_ENV} BKAPP_DEPLOY_ENV=web ${PYTHON} ${MANAGEPY} runserver 0:8000

.PHONY: runserver-enterprise-web
runserver-enterprise-web:
	env ${ENTERPRISE_WEB_ENV} BKAPP_DEPLOY_ENV=web ${PYTHON} ${MANAGEPY} runserver 0:8000

.PHONY: runserver-bkclouds-web
runserver-bkclouds-web:
	env ${BKCLOUDS_ENV} BKAPP_DEPLOY_ENV=web ${PYTHON} ${MANAGEPY} runserver 0:8000

.PHONY: migrate-bkclouds
migrate-bkclouds:
	env ${BKCLOUDS_ENV} ${PYTHON} ${MANAGEPY} createcachetable
	env ${BKCLOUDS_ENV} ${PYTHON} ${MANAGEPY} migrate
	env ${BKCLOUDS_ENV} ${PYTHON} ${MANAGEPY} migrate --database monitor_api

.PHONY: migrate-tencent
migrate-tencent:
	env ${TENCENT_ENV} ${PYTHON} ${MANAGEPY} createcachetable
	env ${TENCENT_ENV} ${PYTHON} ${MANAGEPY} migrate
	env ${TENCENT_ENV} ${PYTHON} ${MANAGEPY} migrate --database monitor_api

.PHONY: i18n-compile
i18n-compile:
	pybabel compile -f -d $(LOCALE_DIR)

.PHONY: i18n
i18n: i18n-python

.PHONY: i18n-updatepython
i18n-updatepython:
	cd $(PROJECT_DIR) && pybabel extract --no-location -F $(BABEL_CONFIG_FILE) -o $(DJANGO_POT_FILE) .
	cd $(PROJECT_DIR) && pybabel update -l en -d $(LOCALE_DIR) -D $(DOMAIN) -i $(DJANGO_POT_FILE)
	cd $(PROJECT_DIR) && pybabel update -l zh_Hans -d $(LOCALE_DIR) -D $(DOMAIN) -i $(DJANGO_POT_FILE)

.PHONY: i18n-update
i18n-update: i18n-updatepython

.PHONY: i18n-python
i18n-python: i18n-updatepython i18n-compile

.PHONY: clean
clean:
	#cd $(PROJECT_DIR) && [ -f $(DJANGO_POT_FILE) ] && rm -rf $(DJANGO_POT_FILE)
	find ${PROJECT_DIR} -name "*.pyc" -delete

.PHONY:code-clean
code-clean:
	find ${PROJECT_DIR} -not -path '*/.*' -name 'test_*.py' -delete || true
	find ${PROJECT_DIR} -not -path '*/.*' -name '*.py' -exec python kernel/script/code_clean.py {} -w -n "${PACK_ENV}" \; || true

.PHONY:code-check
code-check:
	@sh -c 'git ls-tree --name-only `git rev-parse --abbrev-ref HEAD` | grep -v check.sh | while read line; do ./check.sh $$line; done'
	@sh -c 'find -maxdepth 2 -name '__init__.py' -exec dirname {} \; | xargs pylint --rcfile .pylint.conf {}'

.PHONY: git-delete-merged-requests
git-delete-merged-requests:
	git branch --merged | grep -E '^[[:space:]]{1,}[[:digit:]]{1,}-' | xargs git branch -d

.PHONY: npm-install
npm-install:
	cd ${WEBPACK_DIR} && npm i

.PHONY: webpack-build
webpack-build:
	cd ${WEBPACK_DIR} && npm i --unsafe-perm && npm run install-build && npm run build

.PHONY:update-stub
update-stub:
	env ${TENCENT_ENV} BKAPP_DEPLOY_ENV=worker ${PYTHON} ${MANAGEPY} gen_stub -p kernel_api.resource.resource -o ${PROJECT_DIR}/kernel_api/resource/config.pyi

.PHONY: api-config
api-config:
	env ${EE_API_ENV} BKAPP_DEPLOY_ENV=api ${PYTHON} ${MANAGEPY} make_docs -o kernel_api/docs/ -O kernel_api/docs/apidocs/zh_hans --disable_docs --yaml_name monitor.yaml --module kernel_api.views
	env ${EE_API_ENV} BKAPP_DEPLOY_ENV=api ${PYTHON} ${MANAGEPY} make_docs -o kernel_api/docs/extend -O kernel_api/docs/extend/zh_hans --disable_docs --yaml_name monitor_extend.yaml --module kernel_api.extend_views

.PHONY: api-docs
api-docs:
	env ${EE_API_ENV} BKAPP_DEPLOY_ENV=api ${PYTHON} ${MANAGEPY} make_docs -o kernel_api/docs/ -O kernel_api/docs/apidocs/zh_hans --readonly_yaml --yaml_name monitor.yaml --module kernel_api.views
	env ${EE_API_ENV} BKAPP_DEPLOY_ENV=api ${PYTHON} ${MANAGEPY} make_docs -o kernel_api/docs/extend -O kernel_api/docs/extend/zh_hans --readonly_yaml --yaml_name monitor_extend.yaml --module kernel_api.extend_views

.PHONY: check-apis
check-apis:
	env ${EE_API_ENV} BKAPP_DEPLOY_ENV=api ${PYTHON} ${MANAGEPY} check_apis

.PHONY: exend-api-pack
extend-api-pack:
	$(eval package ?= extend)
	$(eval output = /tmp)
	$(eval version = $(shell git describe --dirty="-dev" --always --match "NOT A TAG"))
	$(eval target = moitor_extend_api_${version}.tar.gz)

	rm -rf ${output}/extend_api || true
	mkdir -p ${output}/extend_api/
	cp -r kernel_api/docs/extend ${output}/extend_api/docs
	mv ${output}/extend_api/docs/monitor_extend.yaml ${output}/extend_api/monitor_${package}.yaml
	cp -r kernel_api/extend_* ${output}/extend_api
	find ${output}/extend_api -name "*.pyc" -delete
	cd ${output} && tar cvf ${target} extend_api
	cp ${output}/${target} .

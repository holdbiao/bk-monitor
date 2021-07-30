/**
 * @module: resource.js 
 * @author: 蓝鲸智云
 * @create: Auto generated at 2021-06-10 11:49:24
 */

const localCache = {};

const BaseRestAPI = function (method, url, data, options, async) {
  // 所有请求默认加上bk_biz_id
  if (data) {
    if (!data.bk_biz_id && data.bk_biz_id !== 0) {
      data.bk_biz_id = window.cc_biz_id;
    }
  } else {
    data = {
      bk_biz_id: window.cc_biz_id,
    };
  }
  let allOptions = {
    type: method,
    url: window.site_url + url,
    dataType: "json",
  };

  if (async) {
    allOptions.headers = {
      "X-Async-Task": true,
    };
  }

  allOptions = Object.assign(allOptions, options);
  if (method === "GET") {
    allOptions.data = data;
  } else {
    let isFile = false;
    for (const key in data) {
      const type = String(data[key]);
      if (type === "[object FileList]" || type === "[object File]") {
        isFile = true;
        break;
      }
    }

    if (isFile) {
      const formData = new FormData();
      for (const key in data) {
        formData.append(key, data[key]);
      }
      allOptions.data = formData;
      allOptions.contentType = "multipart/form-data";
      allOptions.processData = false;
      allOptions.contentType = false;
    } else {
      allOptions.data = JSON.stringify(data);
      allOptions.contentType = "application/json";
    }
  }
  const cacheKey = `${url}|${method}|${JSON.stringify(data)}`;

  if (cacheKey in localCache && options && options.cache === true) {
    return localCache[cacheKey];
  } else {
    localCache[cacheKey] = window.$.ajax(allOptions);
    return localCache[cacheKey];
  }
};

/*
  列表类型的API
 */
const RestListAPI = function (method, url) {
  const restAPI = function (data, options) {
    return BaseRestAPI(method, url, data, options);
  };
  restAPI.polling = function (data, callBack, options) {
    return BaseRestAPI(method, url, data, options, true).then(function (
      result
    ) {
      if (result.result) {
        const polling = function () {
          Resource.commons
            .queryAsyncTaskResult(result.data)
            .done(function (pollingResult) {
              if (pollingResult.result) {
                const taskData = pollingResult.data;
                callBack &&
                  callBack(
                    taskData.is_completed,
                    taskData.state,
                    taskData.data,
                    taskData.message
                  );
                if (!taskData.is_completed) {
                  // 若任务未完成，1秒后再次轮询
                  setTimeout(polling, 1000);
                }
              } else {
                // 异常处理
                // eslint-disable-next-line standard/no-callback-literal
                callBack &&
                  callBack(
                    true,
                    "FAILURE",
                    pollingResult.data,
                    pollingResult.message
                  );
              }
            });
        };
        polling();
      } else {
        // 异常处理
        // eslint-disable-next-line standard/no-callback-literal
        callBack && callBack(true, "FAILURE", result.data, result.message);
      }
    });
  };
  return restAPI;
};

/*
  详情类型的API，需要替换掉URL字符串模版中的"{pk}"，以生成合法的URL
 */
const RestDetailAPI = function (method, url) {
  const restAPI = function (id, data, options) {
    const requestURL = url.replace("{pk}", id);
    return BaseRestAPI(method, requestURL, data, options);
  };
  restAPI.polling = function (id, data, callBack, options) {
    const requestURL = url.replace("{pk}", id);
    return BaseRestAPI(method, requestURL, data, options, true).then(function (
      result
    ) {
      if (result.result) {
        const polling = function () {
          Resource.commons
            .queryAsyncTaskResult(result.data)
            .done(function (pollingResult) {
              if (pollingResult.result) {
                const taskData = pollingResult.data;
                callBack &&
                  callBack(
                    taskData.is_completed,
                    taskData.state,
                    taskData.data,
                    taskData.message
                  );
                if (!taskData.is_completed) {
                  setTimeout(polling, 1000);
                }
              } else {
                // 异常处理
                callBack &&
                  callBack(
                    true,
                    "FAILURE",
                    pollingResult.data,
                    pollingResult.message
                  );
              }
            });
        };
        polling();
      } else {
        // 异常处理
        callBack && callBack(true, "FAILURE", result.data, result.message);
      }
    });
  };

  return restAPI;
};

/* Resource API */
const Resource = {

  healthz: {
    
    /**
     * @apiDescription 从配置文件中获取监控配置中主机监控的指标项
     * @api { GET } /rest/v1/healthz/ GetGlobalStatus
     * @apiName GetGlobalStatus
     * @apiGroup healthz
     *
     * @apiSuccess {String} [node_name] Node name
     * @apiSuccess {String} [description] Description
     * @apiSuccess {String} [category] Category
     * @apiSuccess {String} [collect_metric] Collect metric
     * @apiSuccess {String} [collect_args] Collect args
     * @apiSuccess {Integer} [collect_interval] Collect interval
     * @apiSuccess {String} [metric_alias] Metric alias
     * @apiSuccess {String[]} [solution=[]] Solution
     * @apiSuccess {String} [result] Result
     * @apiSuccess {String} [last_update] Last update
     * @apiSuccess {String} [server_ip] Server ip
     *
    */
    getGlobalStatus: RestListAPI('GET', 'rest/v1/healthz/'),
    
    /**
     * 
     * @api { GET } /rest/v1/healthz/graph_point/ ServerGraphPoint
     * @apiName ServerGraphPoint
     * @apiGroup healthz
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} time_range_banner 最近几小时
     * @apiParam {String} host_id 主机ID
     * @apiParam {Integer} index_id 指标ID
     * @apiParam {String} [dimension_field=] 条件字段
     * @apiParam {String} [dimension_field_value=] 条件字段取值
     * @apiParam {String} [group_field=] 维度字段
     * @apiParam {String} [filter_dict={}] 额外过滤参数
     *
     *
    */
    serverGraphPoint: RestListAPI('GET', 'rest/v1/healthz/graph_point/'),
    
    /**
     * 
     * @api { GET } /rest/v1/healthz/host_alarm/ ServerHostAlarm
     * @apiName ServerHostAlarm
     * @apiGroup healthz
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} host_id 主机ID
     * @apiParam {String} alarm_date 日期
     *
     *
    */
    serverHostAlarm: RestListAPI('GET', 'rest/v1/healthz/host_alarm/'),
    
    /**
     * @apiDescription 对job下的根接口进行测试
     * @api { POST } /rest/v1/healthz/job_test_root/ JobTestRootApi
     * @apiName JobTestRootApi
     * @apiGroup healthz
     * @apiParam {String} api_name api名称
     *
     * @apiSuccess {Boolean} status 返回状态
     * @apiSuccess {String} api_name 接口名称
     * @apiSuccess {String} message 返回信息
     * @apiSuccess {String} args 请求参数
     * @apiSuccess {String} result 返回结果
     *
    */
    jobTestRootApi: RestListAPI('POST', 'rest/v1/healthz/job_test_root/'),
    
    /**
     * @apiDescription 对 job 下的非根接口进行测试
     * @api { POST } /rest/v1/healthz/job_test_non_root/ JobTestNonRootApi
     * @apiName JobTestNonRootApi
     * @apiGroup healthz
     * @apiParam {String} api_name api名称
     * @apiParam {String} parent_api 所依赖api
     * @apiParam {String} kwargs 请求参数
     *
     * @apiSuccess {Boolean} status 返回状态
     * @apiSuccess {String} api_name 接口名称
     * @apiSuccess {String} parent_api 父接口名称
     * @apiSuccess {String} message 返回信息
     * @apiSuccess {String} args 请求参数
     * @apiSuccess {String[]} result 返回结果
     *
    */
    jobTestNonRootApi: RestListAPI('POST', 'rest/v1/healthz/job_test_non_root/'),
    
    /**
     * @apiDescription 对cc下的根接口进行测试
     * @api { POST } /rest/v1/healthz/cc_test_root/ CcTestRootApi
     * @apiName CcTestRootApi
     * @apiGroup healthz
     * @apiParam {String} api_name api名称
     *
     * @apiSuccess {Boolean} status 返回状态
     * @apiSuccess {String} api_name 接口名称
     * @apiSuccess {String} message 返回信息
     * @apiSuccess {String} args 请求参数
     * @apiSuccess {String} result 返回结果
     *
    */
    ccTestRootApi: RestListAPI('POST', 'rest/v1/healthz/cc_test_root/'),
    
    /**
     * @apiDescription 对cc下的非根接口进行测试
     * @api { POST } /rest/v1/healthz/cc_test_non_root/ CcTestNonRootApi
     * @apiName CcTestNonRootApi
     * @apiGroup healthz
     * @apiParam {String} api_name api名称
     * @apiParam {String} parent_api 所依赖api
     * @apiParam {String} kwargs 请求参数
     *
     * @apiSuccess {Boolean} status 返回状态
     * @apiSuccess {String} api_name 接口名称
     * @apiSuccess {String} parent_api 父接口名称
     * @apiSuccess {String} message 返回信息
     * @apiSuccess {String} args 请求参数
     * @apiSuccess {String[]} result 返回结果
     *
    */
    ccTestNonRootApi: RestListAPI('POST', 'rest/v1/healthz/cc_test_non_root/'),
    
    /**
     * @apiDescription 对job下的根接口进行测试
     * @api { POST } /rest/v1/healthz/metadata_test_root/ MetadataTestRootApi
     * @apiName MetadataTestRootApi
     * @apiGroup healthz
     * @apiParam {String} api_name api名称
     *
     * @apiSuccess {Boolean} status 返回状态
     * @apiSuccess {String} api_name 接口名称
     * @apiSuccess {String} message 返回信息
     * @apiSuccess {String} args 请求参数
     * @apiSuccess {String} result 返回结果
     *
    */
    metadataTestRootApi: RestListAPI('POST', 'rest/v1/healthz/metadata_test_root/'),
    
    /**
     * @apiDescription 对job下的根接口进行测试
     * @api { POST } /rest/v1/healthz/nodeman_test_root/ NodemanTestRootApi
     * @apiName NodemanTestRootApi
     * @apiGroup healthz
     * @apiParam {String} api_name api名称
     *
     * @apiSuccess {Boolean} status 返回状态
     * @apiSuccess {String} api_name 接口名称
     * @apiSuccess {String} message 返回信息
     * @apiSuccess {String} args 请求参数
     * @apiSuccess {String} result 返回结果
     *
    */
    nodemanTestRootApi: RestListAPI('POST', 'rest/v1/healthz/nodeman_test_root/'),
    
    /**
     * @apiDescription 对bk_data下的根接口进行测试
     * @api { POST } /rest/v1/healthz/bk_data_test_root/ BkDataTestRootApi
     * @apiName BkDataTestRootApi
     * @apiGroup healthz
     * @apiParam {String} api_name api名称
     *
     * @apiSuccess {Boolean} status 返回状态
     * @apiSuccess {String} api_name 接口名称
     * @apiSuccess {String} message 返回信息
     * @apiSuccess {String} args 请求参数
     * @apiSuccess {String} result 返回结果
     *
    */
    bkDataTestRootApi: RestListAPI('POST', 'rest/v1/healthz/bk_data_test_root/'),
    
    /**
     * @apiDescription 对job下的根接口进行测试
     * @api { POST } /rest/v1/healthz/gse_test_root/ GseTestRootApi
     * @apiName GseTestRootApi
     * @apiGroup healthz
     * @apiParam {String} api_name api名称
     *
     * @apiSuccess {Boolean} status 返回状态
     * @apiSuccess {String} api_name 接口名称
     * @apiSuccess {String} message 返回信息
     * @apiSuccess {String} args 请求参数
     * @apiSuccess {String} result 返回结果
     *
    */
    gseTestRootApi: RestListAPI('POST', 'rest/v1/healthz/gse_test_root/'),
    
    /**
     * @apiDescription 获取全部人员选择器成员列表
     * @api { GET } /rest/v1/all_user/ AllUser
     * @apiName AllUser
     * @apiGroup healthz
     *
     *
    */
    allUser: RestListAPI('GET', 'rest/v1/all_user/'),
    
    /**
     * @apiDescription 获取通知配置
     * @api { GET } /rest/v1/alarm_config/ GetAlarmConfig
     * @apiName GetAlarmConfig
     * @apiGroup healthz
     *
     *
    */
    getAlarmConfig: RestListAPI('GET', 'rest/v1/alarm_config/'),
    
    /**
     * @apiDescription 更新通知配置
     * @api { POST } /rest/v1/alarm_config/ UpdateAlarmConfig
     * @apiName UpdateAlarmConfig
     * @apiGroup healthz
     * @apiParam {String} alarm_config 通知设置
     *
     *
    */
    updateAlarmConfig: RestListAPI('POST', 'rest/v1/alarm_config/'),
    
  },

  monitor_api: {
    
  },

  uptime_check: {
    
    /**
     * @apiDescription 监控首页 服务拨测曲线数据获取
    获取规则：
        1. 在没有任务发⽣告警的前提下，默认展示最近添加的最多5个任务曲线
        2. 如果⽤户已特殊关注了N个拨测任务，将替换原有的默认5条线，只展示用户关注的N个任务数据
        3. 若有除⽤户特殊关注的任务以外的任务发⽣告警，则以”橙-红“的渐变⾊，展示用户关注任务+告警任务数据
     * @api { POST } /rest/v2/uptime_check/front_page_data/ FrontPageData
     * @apiName FrontPageData
     * @apiGroup uptime_check
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String[]} task_id_list 拨测任务ID列表
     *
     *
    */
    frontPageData: RestListAPI('POST', 'rest/v2/uptime_check/front_page_data/'),
    
    /**
     * @apiDescription 获取HTTP任务允许设置的Header
     * @api { GET } /rest/v2/uptime_check/get_http_headers/ GetHttpHeaders
     * @apiName GetHttpHeaders
     * @apiGroup uptime_check
     *
     *
    */
    getHttpHeaders: RestListAPI('GET', 'rest/v2/uptime_check/get_http_headers/'),
    
    /**
     * @apiDescription 获取指定拨测任务启用/停用状态
     * @api { POST } /rest/v2/uptime_check/get_strategy_status/ GetStrategyStatus
     * @apiName GetStrategyStatus
     * @apiGroup uptime_check
     * @apiParam {Integer} bk_biz_id Bk biz id
     * @apiParam {String[]} task_id_list Task id list
     *
     *
    */
    getStrategyStatus: RestListAPI('POST', 'rest/v2/uptime_check/get_strategy_status/'),
    
    /**
     * @apiDescription 获取拨测任务详情页面数据
     * @api { GET } /rest/v2/uptime_check/task_detail/ TaskDetail
     * @apiName TaskDetail
     * @apiGroup uptime_check
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} task_id 拨测任务ID
     * @apiParam {String} [time_range] 时间范围
     * @apiParam {String} [location] 地区
     * @apiParam {String} [carrieroperator] 外网运营商
     * @apiParam {String="available","task_duration"} type 数据类型
     * @apiParam {Integer} [time_step] Time step
     *
     *
    */
    taskDetail: RestListAPI('GET', 'rest/v2/uptime_check/task_detail/'),
    
    /**
     * @apiDescription 生成任务详情可用率和响应时长曲线图和地图信息
     * @api { POST } /rest/v2/uptime_check/task_graph_and_map/ TaskGraphAndMap
     * @apiName TaskGraphAndMap
     * @apiGroup uptime_check
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} task_id 拨测任务ID
     * @apiParam {String} [time_range] 时间范围
     * @apiParam {String} [location] 地区
     * @apiParam {String} [carrieroperator] 外网运营商
     *
     *
    */
    taskGraphAndMap: RestListAPI('POST', 'rest/v2/uptime_check/task_graph_and_map/'),
    
    /**
     * 
     * @api { GET } /rest/v2/uptime_check/export_uptime_check_conf/ ExportUptimeCheckConf
     * @apiName ExportUptimeCheckConf
     * @apiGroup uptime_check
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} [task_ids] 拨测任务ID
     * @apiParam {String="TCP","UDP","HTTP"} [protocol] 协议类型
     * @apiParam {String="0","1"} [node_conf_needed=1] 是否需要导出节点配置
     *
     *
    */
    exportUptimeCheckConf: RestListAPI('GET', 'rest/v2/uptime_check/export_uptime_check_conf/'),
    
    /**
     * 
     * @api { GET } /rest/v2/uptime_check/export_uptime_check_node_conf/ ExportUptimeCheckNodeConf
     * @apiName ExportUptimeCheckNodeConf
     * @apiGroup uptime_check
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} [node_ids] 节点ID
     *
     *
    */
    exportUptimeCheckNodeConf: RestListAPI('GET', 'rest/v2/uptime_check/export_uptime_check_node_conf/'),
    
    /**
     * @apiDescription 获取字段映射
     * @api { GET } /rest/v2/uptime_check/import_uptime_check/parse/ FileParse
     * @apiName FileParse
     * @apiGroup uptime_check
     * @apiParam {String="HTTP(S)","TCP","UDP","ICMP"} protocol 任务类型
     *
     *
    */
    fileParse: RestListAPI('GET', 'rest/v2/uptime_check/import_uptime_check/parse/'),
    
    /**
     * @apiDescription 文件模板导入拨测任务resource
     * @api { POST } /rest/v2/uptime_check/import_uptime_check/ FileImportUptimeCheck
     * @apiName FileImportUptimeCheck
     * @apiGroup uptime_check
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String[]} task_list 任务配置列表
     *
     *
    */
    fileImportUptimeCheck: RestListAPI('POST', 'rest/v2/uptime_check/import_uptime_check/'),
    
    /**
     * @apiDescription 节点选择器
     * @api { GET } /rest/v2/uptime_check/select_uptime_check_node/ SelectUptimeCheckNode
     * @apiName SelectUptimeCheckNode
     * @apiGroup uptime_check
     * @apiParam {String} bk_biz_id 业务ID
     *
     *
    */
    selectUptimeCheckNode: RestListAPI('GET', 'rest/v2/uptime_check/select_uptime_check_node/'),
    
    /**
     * @apiDescription 自定义运营商列表
     * @api { GET } /rest/v2/uptime_check/select_carrier_operator/ SelectCarrierOperator
     * @apiName SelectCarrierOperator
     * @apiGroup uptime_check
     * @apiParam {String} bk_biz_id 业务ID
     *
     *
    */
    selectCarrierOperator: RestListAPI('GET', 'rest/v2/uptime_check/select_carrier_operator/'),
    
    /**
     * @apiDescription 拨测目标详情
     * @api { POST } /rest/v2/uptime_check/uptime_check_target_detail/ UptimeCheckTargetDetail
     * @apiName UptimeCheckTargetDetail
     * @apiGroup uptime_check
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} bk_obj_id 目标类型
     * @apiParam {String[]} target_hosts 目标信息
     *
     *
    */
    uptimeCheckTargetDetail: RestListAPI('POST', 'rest/v2/uptime_check/uptime_check_target_detail/'),
    
  },

  plugin: {
    
    /**
     * 
     * @api { POST } /rest/v2/data_dog_plugin/ DataDogPluginUpload
     * @apiName DataDogPluginUpload
     * @apiGroup plugin
     * @apiParam {String} file_data File data
     * @apiParam {String} os Os
     * @apiParam {String} [plugin_id] Plugin id
     *
     *
    */
    dataDogPluginUpload: RestListAPI('POST', 'rest/v2/data_dog_plugin/'),
    
    /**
     * 
     * @api { POST } /rest/v2/metric_plugin/save/ SaveMetric
     * @apiName SaveMetric
     * @apiGroup plugin
     * @apiParam {Object[]} [metric_json=[]] 指标配置
     * @apiParam {String} metric_json.table_name 表名
     * @apiParam {String} metric_json.table_desc 表描述
     * @apiParam {Object[]} metric_json.fields 指标项
     * @apiParam {String} metric_json.fields.description 字段描述
     * @apiParam {String="string","double","int"} metric_json.fields.type 字段类型
     * @apiParam {String="dimension","metric"} metric_json.fields.monitor_type 指标类型
     * @apiParam {String} [metric_json.fields.unit] 单位
     * @apiParam {String} metric_json.fields.name 字段名
     * @apiParam {String} [metric_json.fields.conversion] 换算单位
     * @apiParam {Boolean} [metric_json.fields.is_diff_metric=False] 是否为差值指标
     * @apiParam {Boolean} [metric_json.fields.is_active=True] 是否启用
     * @apiParam {String} [metric_json.fields.source_name=] 原指标名
     * @apiParam {String[]} [metric_json.fields.dimensions] 聚合维度
     * @apiParam {String} plugin_id 插件ID
     * @apiParam {String="Exporter","Script","JMX","DataDog","Pushgateway","Built-In","Log","Process","SNMP_Trap","SNMP"} plugin_type 插件类型
     * @apiParam {Integer} config_version 插件版本
     * @apiParam {Integer} info_version 插件信息版本
     * @apiParam {Boolean} [need_upgrade=False] 是否升级
     *
     *
    */
    saveMetric: RestListAPI('POST', 'rest/v2/metric_plugin/save/'),
    
    /**
     * 
     * @api { POST } /rest/v2/register_plugin/ PluginRegister
     * @apiName PluginRegister
     * @apiGroup plugin
     *
     *
    */
    pluginRegister: RestListAPI('POST', 'rest/v2/register_plugin/'),
    
    /**
     * 
     * @api { POST } /rest/v2/save_and_release_plugin/ SaveAndReleasePlugin
     * @apiName SaveAndReleasePlugin
     * @apiGroup plugin
     *
     *
    */
    saveAndReleasePlugin: RestListAPI('POST', 'rest/v2/save_and_release_plugin/'),
    
    /**
     * 
     * @api { GET } /rest/v2/get_reserved_word/ GetReservedWord
     * @apiName GetReservedWord
     * @apiGroup plugin
     *
     *
    */
    getReservedWord: RestListAPI('GET', 'rest/v2/get_reserved_word/'),
    
    /**
     * @apiDescription 获取插件参数配置和版本发行历史
     * @api { GET } /rest/v2/plugin_upgrade_info/ PluginUpgradeInfo
     * @apiName PluginUpgradeInfo
     * @apiGroup plugin
     * @apiParam {String} plugin_id 插件id
     * @apiParam {String} config_id 配置id
     * @apiParam {Integer} config_version 插件版本
     * @apiParam {Integer} info_version 插件信息版本
     *
     *
    */
    pluginUpgradeInfo: RestListAPI('GET', 'rest/v2/plugin_upgrade_info/'),
    
    /**
     * @apiDescription 获取插件类型
     * @api { GET } /rest/v2/plugin_type/ PluginType
     * @apiName PluginType
     * @apiGroup plugin
     *
     *
    */
    pluginType: RestListAPI('GET', 'rest/v2/plugin_type/'),
    
  },

  collecting: {
    
    /**
     * @apiDescription 获取采集配置列表信息
     * @api { POST } /rest/v2/collecting_config/config_list/ CollectConfigList
     * @apiName CollectConfigList
     * @apiGroup collecting
     * @apiParam {Integer} [bk_biz_id] 业务ID
     * @apiParam {Boolean} [refresh_status] 是否刷新状态
     * @apiParam {String} [search] 搜索字段
     * @apiParam {String} [order] 排序字段
     * @apiParam {Boolean} [disable_service_type=True] 不需要服务分类
     *
     *
    */
    collectConfigList: RestListAPI('POST', 'rest/v2/collecting_config/config_list/'),
    
    /**
     * @apiDescription 获取采集配置详细信息
     * @api { GET } /rest/v2/collecting_config/config_detail/ CollectConfigDetail
     * @apiName CollectConfigDetail
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置ID
     *
     *
    */
    collectConfigDetail: RestListAPI('GET', 'rest/v2/collecting_config/config_detail/'),
    
    /**
     * @apiDescription 获取采集配置详细信息，供前端展示用
     * @api { GET } /rest/v2/collecting_config/frontend_config_detail/ FrontendCollectConfigDetail
     * @apiName FrontendCollectConfigDetail
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置ID
     *
     *
    */
    frontendCollectConfigDetail: RestListAPI('GET', 'rest/v2/collecting_config/frontend_config_detail/'),
    
    /**
     * 
     * @api { GET } /rest/v2/collecting_config/status/ CollectTargetStatus
     * @apiName CollectTargetStatus
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置id
     * @apiParam {String[]} [auto_running_tasks] 自动运行的任务
     *
     *
    */
    collectTargetStatus: RestListAPI('GET', 'rest/v2/collecting_config/status/'),
    
    /**
     * @apiDescription 特意为前端提供的接口，对于前端来说获取主机实例的下发状态和获取topo节点的下发状态是2个接口
     * @api { GET } /rest/v2/collecting_config/node_status/ CollectNodeStatus
     * @apiName CollectNodeStatus
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置id
     * @apiParam {String[]} [auto_running_tasks] 自动运行的任务
     *
     *
    */
    collectNodeStatus: RestListAPI('GET', 'rest/v2/collecting_config/node_status/'),
    
    /**
     * @apiDescription 启停采集配置
     * @api { POST } /rest/v2/collecting_config/toggle/ ToggleCollectConfigStatus
     * @apiName ToggleCollectConfigStatus
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置ID
     * @apiParam {String="enable","disable"} action 启停配置
     *
     *
    */
    toggleCollectConfigStatus: RestListAPI('POST', 'rest/v2/collecting_config/toggle/'),
    
    /**
     * @apiDescription 删除采集配置
     * @api { POST } /rest/v2/collecting_config/delete/ DeleteCollectConfig
     * @apiName DeleteCollectConfig
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置ID
     *
     *
    */
    deleteCollectConfig: RestListAPI('POST', 'rest/v2/collecting_config/delete/'),
    
    /**
     * @apiDescription 克隆采集配置
     * @api { POST } /rest/v2/collecting_config/clone/ CloneCollectConfig
     * @apiName CloneCollectConfig
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置ID
     *
     *
    */
    cloneCollectConfig: RestListAPI('POST', 'rest/v2/collecting_config/clone/'),
    
    /**
     * @apiDescription 重试部分实例或主机
     * @api { POST } /rest/v2/collecting_config/retry/ RetryTargetNodes
     * @apiName RetryTargetNodes
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置ID
     * @apiParam {String[]} target_nodes 需要重试的实例
     * @apiParam {String} steps 重试步骤
     *
     *
    */
    retryTargetNodes: RestListAPI('POST', 'rest/v2/collecting_config/retry/'),
    
    /**
     * @apiDescription 终止部分部署中的实例
     * @api { POST } /rest/v2/collecting_config/revoke/ RevokeTargetNodes
     * @apiName RevokeTargetNodes
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置ID
     * @apiParam {String[]} instance_ids 需要终止的实例ID
     *
     *
    */
    revokeTargetNodes: RestListAPI('POST', 'rest/v2/collecting_config/revoke/'),
    
    /**
     * @apiDescription 批量终止采集配置的部署中的实例
     * @api { POST } /rest/v2/collecting_config/batch_revoke/ BatchRevokeTargetNodes
     * @apiName BatchRevokeTargetNodes
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置ID
     *
     *
    */
    batchRevokeTargetNodes: RestListAPI('POST', 'rest/v2/collecting_config/batch_revoke/'),
    
    /**
     * @apiDescription 批量重试采集配置的失败实例
     * @api { POST } /rest/v2/collecting_config/batch_retry/ BatchRetryConfig
     * @apiName BatchRetryConfig
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置ID
     *
     *
    */
    batchRetryConfig: RestListAPI('POST', 'rest/v2/collecting_config/batch_retry/'),
    
    /**
     * @apiDescription 新增或编辑采集配置
     * @api { POST } /rest/v2/collecting_config/save/ SaveCollectConfig
     * @apiName SaveCollectConfig
     * @apiGroup collecting
     * @apiParam {Integer} [id] 采集配置ID
     * @apiParam {String} name 采集配置名称
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String="Exporter","Script","JMX","DataDog","Pushgateway","Built-In","Log","Process","SNMP_Trap","SNMP"} collect_type 采集方式
     * @apiParam {String="SERVICE","HOST"} target_object_type 采集对象类型
     * @apiParam {String="TOPO","INSTANCE","SERVICE_TEMPLATE","SET_TEMPLATE"} target_node_type 采集目标类型
     * @apiParam {String} plugin_id 插件ID
     * @apiParam {String[]} target_nodes 节点列表
     * @apiParam {Object} [remote_collecting_host=None] 远程采集配置
     * @apiParam {String} remote_collecting_host.ip Ip
     * @apiParam {Integer} remote_collecting_host.bk_cloud_id Bk cloud id
     * @apiParam {Integer} remote_collecting_host.bk_supplier_id Bk supplier id
     * @apiParam {Boolean} remote_collecting_host.is_collecting_only Is collecting only
     * @apiParam {String} params 采集配置参数
     * @apiParam {String} label 二级标签
     * @apiParam {String="EDIT","ADD_DEL"} [operation=EDIT] 操作类型
     *
     *
    */
    saveCollectConfig: RestListAPI('POST', 'rest/v2/collecting_config/save/'),
    
    /**
     * @apiDescription 采集配置插件升级
     * @api { POST } /rest/v2/collecting_config/upgrade/ UpgradeCollectPlugin
     * @apiName UpgradeCollectPlugin
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置id
     * @apiParam {String} params 采集配置参数
     *
     *
    */
    upgradeCollectPlugin: RestListAPI('POST', 'rest/v2/collecting_config/upgrade/'),
    
    /**
     * @apiDescription 采集配置回滚
     * @api { POST } /rest/v2/collecting_config/rollback/ RollbackDeploymentConfig
     * @apiName RollbackDeploymentConfig
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置id
     *
     *
    */
    rollbackDeploymentConfig: RestListAPI('POST', 'rest/v2/collecting_config/rollback/'),
    
    /**
     * @apiDescription 图表resource
     * @api { POST } /rest/v2/collecting_config/graph_point/ GraphPoint
     * @apiName GraphPoint
     * @apiGroup collecting
     * @apiParam {String} metric 指标名
     * @apiParam {String="SUM","AVG","MAX","MIN"} method 聚合方法
     * @apiParam {String} [time_range] 时间范围
     * @apiParam {Integer} id 采集配置id
     * @apiParam {Object[]} [host_list] 主机信息
     * @apiParam {String} host_list.ip 主机IP
     * @apiParam {Integer} host_list.bk_cloud_id 云区域ID
     * @apiParam {String[]} [instance_list] 实例信息
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    graphPoint: RestListAPI('POST', 'rest/v2/collecting_config/graph_point/'),
    
    /**
     * @apiDescription 获取检查视图页左侧topo树
     * @api { POST } /rest/v2/collecting_config/target_status_topo/ FrontendTargetStatusTopo
     * @apiName FrontendTargetStatusTopo
     * @apiGroup collecting
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} id 采集配置ID
     *
     *
    */
    frontendTargetStatusTopo: RestListAPI('POST', 'rest/v2/collecting_config/target_status_topo/'),
    
    /**
     * @apiDescription 获取对应插件版本的指标参数
     * @api { GET } /rest/v2/collecting_config/metrics/ GetMetrics
     * @apiName GetMetrics
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置id
     *
     *
    */
    getMetrics: RestListAPI('GET', 'rest/v2/collecting_config/metrics/'),
    
    /**
     * @apiDescription 编辑采集配置的名称
     * @api { POST } /rest/v2/collecting_config/rename/ RenameCollectConfig
     * @apiName RenameCollectConfig
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置ID
     * @apiParam {String} name 名称
     *
     *
    */
    renameCollectConfig: RestListAPI('POST', 'rest/v2/collecting_config/rename/'),
    
    /**
     * @apiDescription 用于列表页重新进入执行中的采集配置
     * @api { GET } /rest/v2/collecting_config/deployment_diff/ DeploymentConfigDiff
     * @apiName DeploymentConfigDiff
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置id
     *
     *
    */
    deploymentConfigDiff: RestListAPI('GET', 'rest/v2/collecting_config/deployment_diff/'),
    
    /**
     * @apiDescription 获取采集配置下发主机的运行状态
     * @api { GET } /rest/v2/collecting_config/running_status/ CollectRunningStatus
     * @apiName CollectRunningStatus
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置id
     * @apiParam {String[]} [auto_running_tasks] 自动运行的任务
     *
     *
    */
    collectRunningStatus: RestListAPI('GET', 'rest/v2/collecting_config/running_status/'),
    
    /**
     * @apiDescription 获取采集下发单台主机/实例的详细日志信息
     * @api { GET } /rest/v2/collecting_config/get_collect_log_detail/ GetCollectLogDetail
     * @apiName GetCollectLogDetail
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置ID
     * @apiParam {String} instance_id 主机/实例id
     * @apiParam {Integer} task_id 任务id
     *
     *
    */
    getCollectLogDetail: RestListAPI('GET', 'rest/v2/collecting_config/get_collect_log_detail/'),
    
    /**
     * @apiDescription 更新启用中的采集配置的主机总数和异常数
     * @api { GET } /rest/v2/collecting_config/update_config_instance_count/ UpdateConfigInstanceCount
     * @apiName UpdateConfigInstanceCount
     * @apiGroup collecting
     *
     *
    */
    updateConfigInstanceCount: RestListAPI('GET', 'rest/v2/collecting_config/update_config_instance_count/'),
    
    /**
     * 
     * @api { GET } /rest/v2/collecting_config/get_collect_variables/ GetCollectVariables
     * @apiName GetCollectVariables
     * @apiGroup collecting
     *
     *
    */
    getCollectVariables: RestListAPI('GET', 'rest/v2/collecting_config/get_collect_variables/'),
    
    /**
     * 
     * @api { GET } /rest/v2/collecting_config/collect_instance_status/ CollectInstanceStatus
     * @apiName CollectInstanceStatus
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置id
     * @apiParam {String[]} [auto_running_tasks] 自动运行的任务
     *
     *
    */
    collectInstanceStatus: RestListAPI('GET', 'rest/v2/collecting_config/collect_instance_status/'),
    
    /**
     * 
     * @api { POST } /rest/v2/collecting_config/batch_retry_detailed/ BatchRetry
     * @apiName BatchRetry
     * @apiGroup collecting
     * @apiParam {Integer} id 采集配置ID
     *
     *
    */
    batchRetry: RestListAPI('POST', 'rest/v2/collecting_config/batch_retry_detailed/'),
    
    /**
     * @apiDescription 获取各个采集项遗留的订阅配置
     * @api { GET } /rest/v2/collecting_config/list_legacy_subscription/ ListLegacySubscription
     * @apiName ListLegacySubscription
     * @apiGroup collecting
     *
     *
    */
    listLegacySubscription: RestListAPI('GET', 'rest/v2/collecting_config/list_legacy_subscription/'),
    
    /**
     * @apiDescription 停用并删除遗留的订阅配置
    如果是刚下发的升级，这时候订阅id是刚删除的状态，此时需要等半小时再执行清理订阅的操作
     * @api { GET } /rest/v2/collecting_config/clean_legacy_subscription/ CleanLegacySubscription
     * @apiName CleanLegacySubscription
     * @apiGroup collecting
     * @apiParam {Integer[]} subscription_id 节点管理订阅ID
     * @apiParam {String} [action_type=STOP] 动作类型
     * @apiParam {Boolean} [is_force=False] 是否强制清理
     *
     *
    */
    cleanLegacySubscription: RestListAPI('GET', 'rest/v2/collecting_config/clean_legacy_subscription/'),
    
    /**
     * @apiDescription 列出当前配置的告警策略中无效的部分：
    1. 基于日志关键字采集配置了策略，之后又删除了日志关键字；
    2. 基于自定义事件上报配置了策略，之后又删除了自定义事件； 当前配置了策略的自定义事件不让删除
    3. 基于插件对应的采集配置了策略，之后又删除了插件；  暂不考虑该场景
     * @api { GET } /rest/v2/collecting_config/list_legacy_strategy/ ListLegacyStrategy
     * @apiName ListLegacyStrategy
     * @apiGroup collecting
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    listLegacyStrategy: RestListAPI('GET', 'rest/v2/collecting_config/list_legacy_strategy/'),
    
    /**
     * @apiDescription 采集视图配置
     * @api { POST } /rest/v2/collecting_config/get_collect_dashboard_config/ GetCollectDashboardConfig
     * @apiName GetCollectDashboardConfig
     * @apiGroup collecting
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} id 采集ID
     * @apiParam {String} [compare_config=<function GetCollectDashboardConfigResource.RequestSerializer.<lambda> at 0x7fd9f7e53e18>] 对比配置
     * @apiParam {String="leaf_node","topo_node","overview"} [view_type=leaf_node] 视图类型
     *
     *
    */
    getCollectDashboardConfig: RestListAPI('POST', 'rest/v2/collecting_config/get_collect_dashboard_config/'),
    
    /**
     * @apiDescription 列出当前配置的所有相关策略
    1.拿到所有指标的collect_config_ids
    2.找到要删除的采集配置对应的指标
    3.从alarm_item里找到对应的策略ID
    4.返回数据
    - 模糊：返回涉及到的策略ID及名称
    - 精准：查看rt_query_config_id对应的结果表的条件中是否使用了该采集配置
     * @api { POST } /rest/v2/collecting_config/list_related_strategy/ ListRelatedStrategy
     * @apiName ListRelatedStrategy
     * @apiGroup collecting
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} collect_config_id 采集配置ID
     *
     *
    */
    listRelatedStrategy: RestListAPI('POST', 'rest/v2/collecting_config/list_related_strategy/'),
    
    /**
     * @apiDescription 向节点管理轮询任务是否已经初始化完成
     * @api { POST } /rest/v2/collecting_config/is_task_ready/ IsTaskReady
     * @apiName IsTaskReady
     * @apiGroup collecting
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} collect_config_id 采集配置ID
     *
     *
    */
    isTaskReady: RestListAPI('POST', 'rest/v2/collecting_config/is_task_ready/'),
    
  },

  commons: {
    
    /**
     * 
     * @api { GET } /rest/v2/commons/business_list_option/ BusinessListOption
     * @apiName BusinessListOption
     * @apiGroup commons
     *
     *
    */
    businessListOption: RestListAPI('GET', 'rest/v2/commons/business_list_option/'),
    
    /**
     * 
     * @api { GET } /rest/v2/commons/fetch_business_info/ FetchBusinessInfo
     * @apiName FetchBusinessInfo
     * @apiGroup commons
     * @apiParam {Integer} [bk_biz_id=-1] Bk biz id
     *
     *
    */
    fetchBusinessInfo: RestListAPI('GET', 'rest/v2/commons/fetch_business_info/'),
    
    /**
     * @apiDescription 获取文档链接
     * @api { GET } /rest/v2/commons/get_docs_link/ GetDocLink
     * @apiName GetDocLink
     * @apiGroup commons
     * @apiParam {String} md_path 文档路径(md_path)
     *
     *
    */
    getDocLink: RestListAPI('GET', 'rest/v2/commons/get_docs_link/'),
    
    /**
     * @apiDescription 获取国家地区城市列表
     * @api { GET } /rest/v2/commons/country_list/ CountryList
     * @apiName CountryList
     * @apiGroup commons
     *
     *
    */
    countryList: RestListAPI('GET', 'rest/v2/commons/country_list/'),
    
    /**
     * @apiDescription 获取运营商列表
     * @api { GET } /rest/v2/commons/isp_list/ IspList
     * @apiName IspList
     * @apiGroup commons
     *
     *
    */
    ispList: RestListAPI('GET', 'rest/v2/commons/isp_list/'),
    
    /**
     * @apiDescription 主机地区和运营商信息
     * @api { GET } /rest/v2/commons/host_region_isp_info/ HostRegionIspInfo
     * @apiName HostRegionIspInfo
     * @apiGroup commons
     * @apiParam {Integer} bk_biz_id Bk biz id
     * @apiParam {String} [bk_state_name] Bk state name
     * @apiParam {String} [bk_province_name] Bk province name
     * @apiParam {String} [bk_isp_name] Bk isp name
     *
     * @apiSuccess {Integer} plat_id Plat id
     * @apiSuccess {String} plat_name Plat name
     * @apiSuccess {String} ip Ip
     * @apiSuccess {Integer} agent_status Agent status
     * @apiSuccess {String} city City
     * @apiSuccess {String} outer_ip Outer ip
     * @apiSuccess {String} country Country
     * @apiSuccess {String} carrieroperator Carrieroperator
     *
    */
    hostRegionIspInfo: RestListAPI('GET', 'rest/v2/commons/host_region_isp_info/'),
    
    /**
     * 
     * @api { GET } /rest/v2/performance/cc_topo_tree/ CcTopoTree
     * @apiName CcTopoTree
     * @apiGroup commons
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String="host","service"} [instance_type] 对象类型
     *
     *
    */
    ccTopoTree: RestListAPI('GET', 'rest/v2/performance/cc_topo_tree/'),
    
    /**
     * 
     * @api { POST } /rest/v2/commons/get_topo_tree/ GetTopoTree
     * @apiName GetTopoTree
     * @apiGroup commons
     * @apiParam {Integer} bk_biz_id 业务id
     * @apiParam {String="host","service"} [instance_type] 实例类型
     * @apiParam {Boolean} [remove_empty_nodes=False] 是否删除空节点
     *
     *
    */
    getTopoTree: RestListAPI('POST', 'rest/v2/commons/get_topo_tree/'),
    
    /**
     * @apiDescription 获取主机状态
     * @api { POST } /rest/v2/commons/get_host_instance_by_ip/ GetHostInstanceByIp
     * @apiName GetHostInstanceByIp
     * @apiGroup commons
     * @apiParam {Object[]} ip_list Ip list
     * @apiParam {String} ip_list.ip 主机IP
     * @apiParam {Integer} [ip_list.bk_cloud_id] 云区域ID
     * @apiParam {Integer} bk_biz_id Bk biz id
     * @apiParam {Boolean} [with_external_ips=False] With external ips
     *
     *
    */
    getHostInstanceByIp: RestListAPI('POST', 'rest/v2/commons/get_host_instance_by_ip/'),
    
    /**
     * @apiDescription 获取节点下主机状态
     * @api { POST } /rest/v2/commons/get_host_instance_by_node/ GetHostInstanceByNode
     * @apiName GetHostInstanceByNode
     * @apiGroup commons
     * @apiParam {Object[]} node_list Node list
     * @apiParam {String} node_list.bk_obj_id 节点类型
     * @apiParam {Integer} node_list.bk_inst_id 实例ID
     * @apiParam {Integer} node_list.bk_biz_id 业务ID
     * @apiParam {String} [node_list.bk_inst_name] 节点名称
     * @apiParam {Integer} [node_list.SERVICE_TEMPLATE] 所属服务模板ID
     * @apiParam {Integer} [node_list.SET_TEMPLATE] 所属集群模板ID
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Boolean} [with_count=True] 是否需要主机/实例的统计信息
     * @apiParam {Boolean} [with_service_category=True] 是否需要主机信息
     *
     *
    */
    getHostInstanceByNode: RestListAPI('POST', 'rest/v2/commons/get_host_instance_by_node/'),
    
    /**
     * @apiDescription 获取节点服务实例状态
     * @api { POST } /rest/v2/commons/get_service_instance_by_node/ GetServiceInstanceByNode
     * @apiName GetServiceInstanceByNode
     * @apiGroup commons
     * @apiParam {Object[]} node_list Node list
     * @apiParam {String} node_list.bk_obj_id 节点类型
     * @apiParam {Integer} node_list.bk_inst_id 实例ID
     * @apiParam {Integer} node_list.bk_biz_id 业务ID
     * @apiParam {String} [node_list.bk_inst_name] 节点名称
     * @apiParam {Integer} [node_list.SERVICE_TEMPLATE] 所属服务模板ID
     * @apiParam {Integer} [node_list.SET_TEMPLATE] 所属集群模板ID
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Boolean} [with_count=True] 是否需要主机/实例的统计信息
     * @apiParam {Boolean} [with_service_category=True] 是否需要主机信息
     *
     *
    */
    getServiceInstanceByNode: RestListAPI('POST', 'rest/v2/commons/get_service_instance_by_node/'),
    
    /**
     * 
     * @api { POST } /rest/v2/commons/get_service_category/ GetServiceCategory
     * @apiName GetServiceCategory
     * @apiGroup commons
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    getServiceCategory: RestListAPI('POST', 'rest/v2/commons/get_service_category/'),
    
    /**
     * @apiDescription 主机Agent状态
     * @api { POST } /rest/v2/commons/host_agent_status/ HostAgentStatus
     * @apiName HostAgentStatus
     * @apiGroup commons
     * @apiParam {Integer} bk_biz_id Bk biz id
     * @apiParam {String} [search_condition] Search condition
     *
     *
    */
    hostAgentStatus: RestListAPI('POST', 'rest/v2/commons/host_agent_status/'),
    
    /**
     * @apiDescription 获取主线模型
     * @api { GET } /rest/v2/commons/get_mainline_object_topo/ GetMainlineObjectTopo
     * @apiName GetMainlineObjectTopo
     * @apiGroup commons
     *
     *
    */
    getMainlineObjectTopo: RestListAPI('GET', 'rest/v2/commons/get_mainline_object_topo/'),
    
    /**
     * @apiDescription 查询模板列表
     * @api { POST } /rest/v2/commons/get_template/ GetTemplate
     * @apiName GetTemplate
     * @apiGroup commons
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String="SERVICE_TEMPLATE","SET_TEMPLATE"} bk_obj_id 查询对象
     * @apiParam {String="HOST","SERVICE"} bk_inst_type 目标对象类型
     * @apiParam {Boolean} [with_count=False] 需要带节点数量和实例数量返回
     *
     *
    */
    getTemplate: RestListAPI('POST', 'rest/v2/commons/get_template/'),
    
    /**
     * @apiDescription 获取服务模板、集群模板下相应的节点
     * @api { POST } /rest/v2/commons/get_nodes_by_template/ GetNodesByTemplate
     * @apiName GetNodesByTemplate
     * @apiGroup commons
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String="SERVICE_TEMPLATE","SET_TEMPLATE"} bk_obj_id 查询对象
     * @apiParam {String[]} bk_inst_ids 相应的模板ID
     * @apiParam {String="HOST","SERVICE"} bk_inst_type 查询对象下实例的类型
     *
     *
    */
    getNodesByTemplate: RestListAPI('POST', 'rest/v2/commons/get_nodes_by_template/'),
    
    /**
     * @apiDescription 通用图表接口
     * @api { POST } /rest/v2/commons/graph_point/ GraphPoint
     * @apiName GraphPoint
     * @apiGroup commons
     * @apiParam {Integer} [bk_biz_id=0] 业务id
     * @apiParam {String} monitor_field 监控指标对象
     * @apiParam {String} result_table_id rt表名
     * @apiParam {String} [filter_dict=None] 自定义过滤条件
     * @apiParam {String[]} [group_by_list=None] 聚合字段
     * @apiParam {String} [method=MEAN] 聚合方法
     * @apiParam {String} [unit=] 单位
     * @apiParam {Number} [conversion=1] 转换除数
     * @apiParam {String} [series_name=] 指标名称
     * @apiParam {Integer} [view_width=12] 宽度
     * @apiParam {Integer} [interval=1] 采集间隔
     * @apiParam {Integer} [time_step=0] 指定数据点频率
     * @apiParam {Boolean} [use_short_series_name=False] 是否使用短指标名
     * @apiParam {String} [time_range] 时间范围
     * @apiParam {Integer} [time_start] 开始时间
     * @apiParam {Integer} [time_end] 结束时间
     * @apiParam {String} [extend_fields={}] 日志需要的额外字段
     * @apiParam {String} [data_source_label=] 数据来源
     * @apiParam {String} [data_type_label=] 数据类型
     *
     *
    */
    graphPoint: RestListAPI('POST', 'rest/v2/commons/graph_point/'),
    
    /**
     * @apiDescription 获取业务下的结果表列表（包含全业务）
     * @api { GET } /rest/v2/commons/get_context/ GetContext
     * @apiName GetContext
     * @apiGroup commons
     * @apiParam {Integer} [bk_biz_id] 业务ID
     *
     *
    */
    getContext: RestListAPI('GET', 'rest/v2/commons/get_context/'),
    
    /**
     * @apiDescription 获取业务下的结果表列表（包含全业务）
     * @api { GET } /rest/v2/commons/list_result_table_access_info/ ListResultTableAccessInfo
     * @apiName ListResultTableAccessInfo
     * @apiGroup commons
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     * @apiSuccess {String} id 结果表名称
     * @apiSuccess {String[]} storages 存储类型
     * @apiSuccess {String} description 结果表描述
     * @apiSuccess {Integer} count_freq 监控周期（秒）
     * @apiSuccess {Object[]} fields 结果表字段列表
     * @apiSuccess {String} fields.field 字段名称
     * @apiSuccess {String} fields.description 字段描述
     * @apiSuccess {Boolean} fields.is_dimension 是否为维度字段
     * @apiSuccess {String} [fields.processor=None] 聚合方法
     * @apiSuccess {String} [fields.processor_args=None] 聚合方法参数
     * @apiSuccess {Boolean} is_statistical 是否为统计结果表
     * @apiSuccess {Boolean} need_access 是否需要接入
     * @apiSuccess {String} [rt_id_backend] 未处理的rt表
     *
    */
    listResultTableAccessInfo: RestListAPI('GET', 'rest/v2/commons/list_result_table_access_info/'),
    
    /**
     * @apiDescription 根据结果表ID获取结果表信息
     * @api { GET } /rest/v2/commons/get_result_table/ GetResultTableAccessInfo
     * @apiName GetResultTableAccessInfo
     * @apiGroup commons
     * @apiParam {Integer} bk_biz_id 业务 ID
     * @apiParam {String} id 结果表ID
     *
     * @apiSuccess {String} id 结果表名称
     * @apiSuccess {String[]} storages 存储类型
     * @apiSuccess {String} description 结果表描述
     * @apiSuccess {Integer} count_freq 监控周期（秒）
     * @apiSuccess {Object[]} fields 结果表字段列表
     * @apiSuccess {String} fields.field 字段名称
     * @apiSuccess {String} fields.description 字段描述
     * @apiSuccess {Boolean} fields.is_dimension 是否为维度字段
     * @apiSuccess {String} [fields.processor=None] 聚合方法
     * @apiSuccess {String} [fields.processor_args=None] 聚合方法参数
     * @apiSuccess {Boolean} is_statistical 是否为统计结果表
     * @apiSuccess {Boolean} need_access 是否需要接入
     * @apiSuccess {String} [rt_id_backend] 未处理的rt表
     *
    */
    getResultTableAccessInfo: RestListAPI('GET', 'rest/v2/commons/get_result_table/'),
    
    /**
     * @apiDescription 列出结果表的分类标签
     * @api { GET } /rest/v2/commons/get_label/ GetLabel
     * @apiName GetLabel
     * @apiGroup commons
     * @apiParam {String} [label_type=result_table_label] 标签类别
     * @apiParam {Integer} [level] 标签层级
     * @apiParam {Boolean} [include_admin_only=True] 是否展示管理员标签
     *
     *
    */
    getLabel: RestListAPI('GET', 'rest/v2/commons/get_label/'),
    
    /**
     * @apiDescription 通用文件上传接口
     * @api { POST } /rest/v2/commons/file_upload/ FileUpload
     * @apiName FileUpload
     * @apiGroup commons
     * @apiParam {String} file_data File data
     * @apiParam {String} [path=] Path
     * @apiParam {String} [file_name] File name
     *
     *
    */
    fileUpload: RestListAPI('POST', 'rest/v2/commons/file_upload/'),
    
    /**
     * @apiDescription 通用文件分发接口
     * @api { POST } /rest/v2/commons/file_deploy/ FileDeploy
     * @apiName FileDeploy
     * @apiGroup commons
     * @apiParam {Integer} bk_biz_id Bk biz id
     * @apiParam {String} operator Operator
     * @apiParam {String[]} file_ids File ids
     * @apiParam {String[]} hosts Hosts
     * @apiParam {String} target_path Target path
     *
     *
    */
    fileDeploy: RestListAPI('POST', 'rest/v2/commons/file_deploy/'),
    
    /**
     * @apiDescription 查询Resource异步任务状态
     * @api { GET } /rest/v2/commons/query_async_task_result/ QueryAsyncTaskResult
     * @apiName QueryAsyncTaskResult
     * @apiGroup commons
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} task_id 任务ID
     *
     *
    */
    queryAsyncTaskResult: RestListAPI('GET', 'rest/v2/commons/query_async_task_result/'),
    
    /**
     * 
     * @api { GET } /rest/v2/commons/get_footer/ GetFooter
     * @apiName GetFooter
     * @apiGroup commons
     *
     *
    */
    getFooter: RestListAPI('GET', 'rest/v2/commons/get_footer/'),
    
  },

  overview: {
    
    /**
     * @apiDescription 告警类型排行
     * @api { GET } /rest/v2/overview/alarm_rank/ AlarmRank
     * @apiName AlarmRank
     * @apiGroup overview
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} [days=7] 统计天数
     *
     *
    */
    alarmRank: RestListAPI('GET', 'rest/v2/overview/alarm_rank/'),
    
    /**
     * @apiDescription 告警数量信息
     * @api { GET } /rest/v2/overview/alarm_count_info/ AlarmCountInfo
     * @apiName AlarmCountInfo
     * @apiGroup overview
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    alarmCountInfo: RestListAPI('GET', 'rest/v2/overview/alarm_count_info/'),
    
    /**
     * @apiDescription 主机性能分布
     * @api { GET } /rest/v2/overview/host_performance_distribution/ HostPerformanceDistribution
     * @apiName HostPerformanceDistribution
     * @apiGroup overview
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    hostPerformanceDistribution: RestListAPI('GET', 'rest/v2/overview/host_performance_distribution/'),
    
    /**
     * @apiDescription 业务监控状态总览
     * @api { GET } /rest/v2/overview/monitor_info/ MonitorInfo
     * @apiName MonitorInfo
     * @apiGroup overview
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    monitorInfo: RestListAPI('GET', 'rest/v2/overview/monitor_info/'),
    
  },

  performance: {
    
    /**
     * 
     * @api { GET } /rest/v2/performance/cc_topo_tree/ CcTopoTree
     * @apiName CcTopoTree
     * @apiGroup performance
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    ccTopoTree: RestListAPI('GET', 'rest/v2/performance/cc_topo_tree/'),
    
    /**
     * 
     * @api { GET } /rest/v2/performance/agent_status/ AgentStatus
     * @apiName AgentStatus
     * @apiGroup performance
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} host_id 主机ID
     *
     *
    */
    agentStatus: RestListAPI('GET', 'rest/v2/performance/agent_status/'),
    
    /**
     * 
     * @api { GET } /rest/v2/performance/host_alarm/count/ HostAlarmCount
     * @apiName HostAlarmCount
     * @apiGroup performance
     * @apiParam {String} host_id_list 主机ID（批量）
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} [days=7] 查询时间
     *
     *
    */
    hostAlarmCount: RestListAPI('GET', 'rest/v2/performance/host_alarm/count/'),
    
    /**
     * 
     * @api { GET } /rest/v2/performance/host_index/ HostIndex
     * @apiName HostIndex
     * @apiGroup performance
     *
     *
    */
    hostIndex: RestListAPI('GET', 'rest/v2/performance/host_index/'),
    
    /**
     * 
     * @api { POST } /rest/v2/performance/host_index/field_values/ GetFieldValuesByIndexId
     * @apiName GetFieldValuesByIndexId
     * @apiGroup performance
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     * @apiParam {Integer} index_id 指标ID
     * @apiParam {String} field 查询的维度字段
     * @apiParam {String} [condition={}] 查询条件
     *
     *
    */
    getFieldValuesByIndexId: RestListAPI('POST', 'rest/v2/performance/host_index/field_values/'),
    
    /**
     * 
     * @api { POST } /rest/v2/performance/host_index/graph_point/ GraphPoint
     * @apiName GraphPoint
     * @apiGroup performance
     * @apiParam {String} [bk_biz_id=0] 业务ID
     * @apiParam {String} [time_range] 时间范围
     * @apiParam {Object[]} ip_list 主机列表
     * @apiParam {String} ip_list.ip 主机IP
     * @apiParam {Integer} ip_list.bk_cloud_id 云区域ID
     * @apiParam {Integer} index_id 指标ID
     * @apiParam {String} [dimension_field=] 条件字段
     * @apiParam {String} [dimension_field_value=] 条件字段取值
     * @apiParam {String[]} [group_fields=[]] 维度字段
     * @apiParam {String} [filter_dict={}] 额外过滤参数
     * @apiParam {Integer} [time_step] Time step
     *
     *
    */
    graphPoint: RestListAPI('POST', 'rest/v2/performance/host_index/graph_point/'),
    
    /**
     * 
     * @api { GET } /rest/v2/performance/host_component_info/ HostComponentInfo
     * @apiName HostComponentInfo
     * @apiGroup performance
     * @apiParam {String} bk_biz_id 业务ID
     * @apiParam {String} ip IP
     * @apiParam {String} bk_cloud_id 云区域ID
     * @apiParam {String} name 组件名称
     *
     *
    */
    hostComponentInfo: RestListAPI('GET', 'rest/v2/performance/host_component_info/'),
    
    /**
     * 
     * @api { POST } /rest/v2/performance/host_performance_detail/ HostPerformanceDetail
     * @apiName HostPerformanceDetail
     * @apiGroup performance
     * @apiParam {String} ip IP
     * @apiParam {Integer} [bk_cloud_id] 云区域ID
     * @apiParam {Integer} bk_biz_id 业务id
     *
     *
    */
    hostPerformanceDetail: RestListAPI('POST', 'rest/v2/performance/host_performance_detail/'),
    
    /**
     * 
     * @api { POST } /rest/v2/performance/host_topo_node_detail/ HostTopoNodeDetail
     * @apiName HostTopoNodeDetail
     * @apiGroup performance
     * @apiParam {Integer} bk_biz_id 业务id
     * @apiParam {String} bk_obj_id 节点类型
     * @apiParam {Integer} bk_inst_id 节点实例ID
     *
     *
    */
    hostTopoNodeDetail: RestListAPI('POST', 'rest/v2/performance/host_topo_node_detail/'),
    
    /**
     * 
     * @api { POST } /rest/v2/performance/host_process_status/ HostProcessStatus
     * @apiName HostProcessStatus
     * @apiGroup performance
     * @apiParam {String} ip IP
     * @apiParam {Integer} bk_cloud_id 云区域ID
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    hostProcessStatus: RestListAPI('POST', 'rest/v2/performance/host_process_status/'),
    
    /**
     * @apiDescription 获取拓扑下的进程
     * @api { POST } /rest/v2/performance/topo_node_process_status/ TopoNodeProcessStatus
     * @apiName TopoNodeProcessStatus
     * @apiGroup performance
     * @apiParam {Integer} bk_biz_id 业务id
     * @apiParam {String} bk_obj_id 节点类型
     * @apiParam {Integer} bk_inst_id 节点实例ID
     *
     *
    */
    topoNodeProcessStatus: RestListAPI('POST', 'rest/v2/performance/topo_node_process_status/'),
    
    /**
     * @apiDescription 获取主机列表信息
     * @api { GET } /rest/v2/performance/host_list/ HostPerformance
     * @apiName HostPerformance
     * @apiGroup performance
     * @apiParam {Integer} [bk_biz_id] 业务ID
     *
     *
    */
    hostPerformance: RestListAPI('GET', 'rest/v2/performance/host_list/'),
    
    /**
     * 
     * @api { POST } /rest/v2/performance/get_host_dashboard_config/ GetHostDashboardConfig
     * @apiName GetHostDashboardConfig
     * @apiGroup performance
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String="host","process"} type 类型
     * @apiParam {String} [compare_config=<function GetHostDashboardConfigResource.RequestSerializer.<lambda> at 0x7fd9f80ada60>] 对比配置
     *
     *
    */
    getHostDashboardConfig: RestListAPI('POST', 'rest/v2/performance/get_host_dashboard_config/'),
    
    /**
     * @apiDescription 获取主机拓扑的视图面板
     * @api { POST } /rest/v2/performance/get_topo_node_dashboard_config/ GetTopoNodeDashboardConfig
     * @apiName GetTopoNodeDashboardConfig
     * @apiGroup performance
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String="host","process"} type 类型
     * @apiParam {String} [compare_config=<function GetHostDashboardConfigResource.RequestSerializer.<lambda> at 0x7fd9f80ada60>] 对比配置
     *
     *
    */
    getTopoNodeDashboardConfig: RestListAPI('POST', 'rest/v2/performance/get_topo_node_dashboard_config/'),
    
    /**
     * @apiDescription 主机信息查询
     * @api { POST } /rest/v2/performance/search_host_info/ SearchHostInfo
     * @apiName SearchHostInfo
     * @apiGroup performance
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    searchHostInfo: RestListAPI('POST', 'rest/v2/performance/search_host_info/'),
    
    /**
     * 
     * @api { POST } /rest/v2/performance/search_host_metric/ SearchHostMetric
     * @apiName SearchHostMetric
     * @apiGroup performance
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String[]} [ips] 主机IP信息
     *
     *
    */
    searchHostMetric: RestListAPI('POST', 'rest/v2/performance/search_host_metric/'),
    
  },

  notice_group: {
    
    /**
     * @apiDescription 获取平台全部的通知对象
     * @api { GET } /rest/v2/notice_group/get_receiver/ GetReceiver
     * @apiName GetReceiver
     * @apiGroup notice_group
     * @apiParam {Integer} [bk_biz_id] 业务Id
     *
     *
    */
    getReceiver: RestListAPI('GET', 'rest/v2/notice_group/get_receiver/'),
    
    /**
     * @apiDescription 获取平台全部的通知方式
     * @api { GET } /rest/v2/notice_group/get_notice_way/ GetNoticeWay
     * @apiName GetNoticeWay
     * @apiGroup notice_group
     * @apiParam {Boolean} [show_all=False] 是否展示全部
     *
     *
    */
    getNoticeWay: RestListAPI('GET', 'rest/v2/notice_group/get_notice_way/'),
    
    /**
     * @apiDescription 创建、修改通知组
     * @api { POST } /rest/v2/notice_group/notice_group_config/ NoticeGroupConfig
     * @apiName NoticeGroupConfig
     * @apiGroup notice_group
     *
     *
    */
    noticeGroupConfig: RestListAPI('POST', 'rest/v2/notice_group/notice_group_config/'),
    
    /**
     * @apiDescription 删除通知组
     * @api { POST } /rest/v2/notice_group/delete_notice_group/ DeleteNoticeGroup
     * @apiName DeleteNoticeGroup
     * @apiGroup notice_group
     * @apiParam {String[]} id_list 通知组ID
     *
     *
    */
    deleteNoticeGroup: RestListAPI('POST', 'rest/v2/notice_group/delete_notice_group/'),
    
    /**
     * @apiDescription 获取通知组列表
     * @api { GET } /rest/v2/notice_group/notice_group_list/ NoticeGroupList
     * @apiName NoticeGroupList
     * @apiGroup notice_group
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     *
     *
    */
    noticeGroupList: RestListAPI('GET', 'rest/v2/notice_group/notice_group_list/'),
    
    /**
     * @apiDescription 获取通知组详情
     * @api { GET } /rest/v2/notice_group/notice_group_detail/ NoticeGroupDetail
     * @apiName NoticeGroupDetail
     * @apiGroup notice_group
     * @apiParam {Integer} id 通知組ID
     *
     *
    */
    noticeGroupDetail: RestListAPI('GET', 'rest/v2/notice_group/notice_group_detail/'),
    
  },

  strategies: {
    
    /**
     * @apiDescription 获取平台全部的监控对象
     * @api { GET } /rest/v2/strategies/get_scenario_list/ GetScenarioList
     * @apiName GetScenarioList
     * @apiGroup strategies
     *
     *
    */
    getScenarioList: RestListAPI('GET', 'rest/v2/strategies/get_scenario_list/'),
    
    /**
     * 
     * @api { POST } /rest/v2/strategies/get_metric_list/ GetMetricList
     * @apiName GetMetricList
     * @apiGroup strategies
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} [data_source_label=] 指标数据来源
     * @apiParam {String} [data_type_label=] 指标数据类型
     * @apiParam {String} [result_table_label=] 对象类型
     * @apiParam {String} [tag=] 标签
     * @apiParam {String} [search_fields=<function GetMetricListResource.RequestSerializer.<lambda> at 0x7fd9f83d4378>] 查询字段
     * @apiParam {Boolean} [is_exact_match=False] 是否精确匹配
     * @apiParam {String} [search_value=] 查询关键字
     * @apiParam {Integer} [page] 页码
     * @apiParam {Integer} [page_size] 每页数目
     *
     *
    */
    getMetricList: RestListAPI('POST', 'rest/v2/strategies/get_metric_list/'),
    
    /**
     * @apiDescription 获取指标维度最近上报的值
     * @api { POST } /rest/v2/strategies/get_dimension_values/ GetDimensionValues
     * @apiName GetDimensionValues
     * @apiGroup strategies
     * @apiParam {String} result_table_id 结果表名
     * @apiParam {String} metric_field 指标名
     * @apiParam {String} field 维度名
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     * @apiParam {String} [filter_dict={}] 过滤条件
     * @apiParam {String[]} [where=[]] 查询条件
     *
     *
    */
    getDimensionValues: RestListAPI('POST', 'rest/v2/strategies/get_dimension_values/'),
    
    /**
     * @apiDescription 创建、修改监控策略
     * @api { POST } /rest/v2/strategies/strategy_config/ StrategyConfig
     * @apiName StrategyConfig
     * @apiGroup strategies
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 策略名称
     * @apiParam {String} scenario 监控场景
     * @apiParam {Object[]} item_list 监控算法配置
     * @apiParam {Integer} [item_list.id] item_id
     * @apiParam {String} item_list.name 监控指标别名
     * @apiParam {String} item_list.metric_field 监控指标别名
     * @apiParam {String} item_list.data_source_label 数据来源标签
     * @apiParam {String} item_list.data_type_label 数据类型标签
     * @apiParam {String} [item_list.result_table_id] 表名
     * @apiParam {String} [item_list.agg_method] 聚合算法
     * @apiParam {String} [item_list.agg_interval] 聚合周期
     * @apiParam {String[]} [item_list.agg_dimension] 聚合维度
     * @apiParam {String[]} [item_list.agg_condition] 聚合条件
     * @apiParam {String} [item_list.unit] 单位
     * @apiParam {Number} [item_list.unit_conversion=1.0] 单位换算
     * @apiParam {Object[]} item_list.detect_algorithm_list 检测算法列表
     * @apiParam {Integer} item_list.detect_algorithm_list.level 告警级别
     * @apiParam {Object[]} item_list.detect_algorithm_list.algorithm_list 检测算法列表
     * @apiParam {String} item_list.detect_algorithm_list.algorithm_list.algorithm_config 检测算法配置
     * @apiParam {String="","Threshold","PartialNodes","SimpleRingRatio","AdvancedRingRatio","SimpleYearRound","AdvancedYearRound","OsRestart","ProcPort","YearRoundAmplitude","YearRoundRange","RingRatioAmplitude","PingUnreachable","IntelligentDetect"} item_list.detect_algorithm_list.algorithm_list.algorithm_type 检测算法
     * @apiParam {String} [item_list.detect_algorithm_list.algorithm_list.algorithm_unit=] 算法单位
     * @apiParam {String} [item_list.trigger_config={}] 告警触发配置
     * @apiParam {String} [item_list.recovery_config={}] 告警恢复配置
     * @apiParam {String} [item_list.rule] 组合方式
     * @apiParam {String} [item_list.extend_fields={}] 扩展字段
     * @apiParam {String} [item_list.keywords] 组合字段
     * @apiParam {String} [item_list.keywords_query_string] 关键字查询条件
     * @apiParam {String[]} [item_list.target=[[]]] 策略目标
     * @apiParam {String} no_data_config 无数据告警配置
     * @apiParam {String} [message_template] 告警模板
     * @apiParam {Object[]} action_list 触发动作
     * @apiParam {Integer} [action_list.id] action_id
     * @apiParam {String} [action_list.action_type=notice] 触发动作
     * @apiParam {String} action_list.config 告警相关配置
     * @apiParam {String[]} [action_list.notice_group_list] 通知组ID列表
     * @apiParam {Integer} [id] 策略ID
     * @apiParam {String} source_type 策略配置来源
     * @apiParam {Boolean} [is_enabled=True] Is enabled
     * @apiParam {String[]} [labels] Labels
     *
     *
    */
    strategyConfig: RestListAPI('POST', 'rest/v2/strategies/strategy_config/'),
    
    /**
     * @apiDescription 拷贝监控策略
     * @api { POST } /rest/v2/strategies/clone_strategy_config/ CloneStrategyConfig
     * @apiName CloneStrategyConfig
     * @apiGroup strategies
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} id 策略ID
     *
     *
    */
    cloneStrategyConfig: RestListAPI('POST', 'rest/v2/strategies/clone_strategy_config/'),
    
    /**
     * @apiDescription 删除监控策略
     * @api { POST } /rest/v2/strategies/delete_strategy_config/ DeleteStrategyConfig
     * @apiName DeleteStrategyConfig
     * @apiGroup strategies
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} [id] 策略ID
     * @apiParam {String[]} [ids] 策略ID列表
     *
     *
    */
    deleteStrategyConfig: RestListAPI('POST', 'rest/v2/strategies/delete_strategy_config/'),
    
    /**
     * @apiDescription 获取监控策略列表
     * @api { POST } /rest/v2/strategies/strategy_config_list/ StrategyConfigList
     * @apiName StrategyConfigList
     * @apiGroup strategies
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     * @apiParam {Integer} [bk_cloud_id] 云区域ID
     * @apiParam {String} [order_by=-update_time] 排序字段
     * @apiParam {String} [scenario] 二级标签
     * @apiParam {Integer} [page] 页码
     * @apiParam {Integer} [page_size] 每页条数
     * @apiParam {String} [notice_group_name] 告警组名称
     * @apiParam {String} [service_category] 服务分类
     * @apiParam {Integer} [task_id] 任务ID
     * @apiParam {String} [IP] IP筛选
     * @apiParam {String} [metric_id] 指标ID
     * @apiParam {String[]} [ids] ID列表
     * @apiParam {Integer} [bk_event_group_id] 事件分组ID
     * @apiParam {String[]} [data_source_list] 数据来源列表
     * @apiParam {String[]} [conditions] 搜索条件
     * @apiParam {Integer} [only_using=0] 仅统计在用的类型
     *
     *
    */
    strategyConfigList: RestListAPI('POST', 'rest/v2/strategies/strategy_config_list/'),
    
    /**
     * @apiDescription 获取监控策略详情
     * @api { GET } /rest/v2/strategies/strategy_config_detail/ StrategyConfigDetail
     * @apiName StrategyConfigDetail
     * @apiGroup strategies
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} id 策略ID
     *
     *
    */
    strategyConfigDetail: RestListAPI('GET', 'rest/v2/strategies/strategy_config_detail/'),
    
    /**
     * @apiDescription 批量修改接口
     * @api { POST } /rest/v2/strategies/bulk_edit_strategy/ BulkEditStrategy
     * @apiName BulkEditStrategy
     * @apiGroup strategies
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String[]} id_list 批量修改的策略ID列表
     * @apiParam {String} edit_data 批量修改的值
     *
     *
    */
    bulkEditStrategy: RestListAPI('POST', 'rest/v2/strategies/bulk_edit_strategy/'),
    
    /**
     * @apiDescription 获取指标对应的维度列表
     * @api { GET } /rest/v2/strategies/get_dimension_list/ GetDimensionList
     * @apiName GetDimensionList
     * @apiGroup strategies
     * @apiParam {String} [data_source_label] 数据来源
     * @apiParam {String} [data_type_label] 数据类型
     * @apiParam {String} [result_table_id] 表名
     * @apiParam {Integer} [custom_event_id] 自定义事件ID
     * @apiParam {Integer} [bk_event_group_id] 自定义事件组ID
     * @apiParam {Boolean} [show_all=False] 是否展示全部维度
     *
     *
    */
    getDimensionList: RestListAPI('GET', 'rest/v2/strategies/get_dimension_list/'),
    
    /**
     * @apiDescription 获取监控策略轻量列表，供告警屏蔽选择策略配置时使用
     * @api { GET } /rest/v2/strategies/plain_strategy_list/ PlainStrategyList
     * @apiName PlainStrategyList
     * @apiGroup strategies
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     * @apiParam {Integer} [bk_cloud_id] 云区域ID
     * @apiParam {String} [order_by=-update_time] 排序字段
     * @apiParam {String} [scenario] 二级标签
     * @apiParam {Integer} [page] 页码
     * @apiParam {Integer} [page_size] 每页条数
     * @apiParam {String} [notice_group_name] 告警组名称
     * @apiParam {String} [service_category] 服务分类
     * @apiParam {Integer} [task_id] 任务ID
     * @apiParam {String} [IP] IP筛选
     * @apiParam {String} [metric_id] 指标ID
     * @apiParam {String[]} [ids] ID列表
     * @apiParam {Integer} [bk_event_group_id] 事件分组ID
     * @apiParam {String[]} [data_source_list] 数据来源列表
     * @apiParam {String[]} [conditions] 搜索条件
     * @apiParam {Integer} [only_using=0] 仅统计在用的类型
     *
     *
    */
    plainStrategyList: RestListAPI('GET', 'rest/v2/strategies/plain_strategy_list/'),
    
    /**
     * @apiDescription 获取监控策略信息，供告警屏蔽策略展示用
     * @api { GET } /rest/v2/strategies/strategy_info/ StrategyInfo
     * @apiName StrategyInfo
     * @apiGroup strategies
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} id 策略ID
     *
     *
    */
    strategyInfo: RestListAPI('GET', 'rest/v2/strategies/strategy_info/'),
    
    /**
     * @apiDescription 获取告警模板变量列表
     * @api { GET } /rest/v2/strategies/notice_variable_list/ NoticeVariableList
     * @apiName NoticeVariableList
     * @apiGroup strategies
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    noticeVariableList: RestListAPI('GET', 'rest/v2/strategies/notice_variable_list/'),
    
    /**
     * @apiDescription 获取索引集
     * @api { GET } /rest/v2/strategies/get_index_set_list/ GetIndexSetList
     * @apiName GetIndexSetList
     * @apiGroup strategies
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} [index_set_id=-1] 查询索引集
     *
     *
    */
    getIndexSetList: RestListAPI('GET', 'rest/v2/strategies/get_index_set_list/'),
    
    /**
     * @apiDescription 获取日志关键字的维度
     * @api { GET } /rest/v2/strategies/get_log_fields/ GetLogFields
     * @apiName GetLogFields
     * @apiGroup strategies
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} index_set_id 索引集ID
     *
     *
    */
    getLogFields: RestListAPI('GET', 'rest/v2/strategies/get_log_fields/'),
    
    /**
     * @apiDescription 通知模板预渲染
     * @api { POST } /rest/v2/strategies/render_notice_template/ RenderNoticeTemplate
     * @apiName RenderNoticeTemplate
     * @apiGroup strategies
     * @apiParam {String} scenario 场景
     * @apiParam {String} template 消息模板
     *
     *
    */
    renderNoticeTemplate: RestListAPI('POST', 'rest/v2/strategies/render_notice_template/'),
    
    /**
     * @apiDescription 获取指标单位列表
     * @api { GET } /rest/v2/strategies/get_unit_list/ GetUnitList
     * @apiName GetUnitList
     * @apiGroup strategies
     *
     *
    */
    getUnitList: RestListAPI('GET', 'rest/v2/strategies/get_unit_list/'),
    
    /**
     * @apiDescription 获取指标单位详细信息
     * @api { GET } /rest/v2/strategies/get_unit_info/ GetUnitInfo
     * @apiName GetUnitInfo
     * @apiGroup strategies
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     * @apiParam {String} unit_id 二级标签
     *
     *
    */
    getUnitInfo: RestListAPI('GET', 'rest/v2/strategies/get_unit_info/'),
    
    /**
     * @apiDescription 创建/修改策略标签
     * @api { POST } /rest/v2/strategies/strategy_label/ StrategyLabel
     * @apiName StrategyLabel
     * @apiGroup strategies
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     * @apiParam {Integer} [strategy_id=0] 策略ID
     * @apiParam {String} [id=None] 标签ID
     * @apiParam {String} label_name 标签名
     *
     *
    */
    strategyLabel: RestListAPI('POST', 'rest/v2/strategies/strategy_label/'),
    
    /**
     * @apiDescription 获取策略标签列表
     * @api { GET } /rest/v2/strategies/strategy_label_list/ StrategyLabelList
     * @apiName StrategyLabelList
     * @apiGroup strategies
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     * @apiParam {Integer} [strategy_id=0] 策略ID
     *
     *
    */
    strategyLabelList: RestListAPI('GET', 'rest/v2/strategies/strategy_label_list/'),
    
    /**
     * @apiDescription 删除策略标签
     * @api { POST } /rest/v2/strategies/delete_strategy_label/ DeleteStrategyLabel
     * @apiName DeleteStrategyLabel
     * @apiGroup strategies
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     * @apiParam {Integer} [strategy_id=0] 策略ID
     * @apiParam {String} [label_name=] 标签名
     *
     *
    */
    deleteStrategyLabel: RestListAPI('POST', 'rest/v2/strategies/delete_strategy_label/'),
    
    /**
     * @apiDescription 获取指定Item Metric_id的策略配置及告警情况
    return: {
        "{metric_id}": 0,1,2 # 0:未配置策略, 1:配置了策略, 2: 告警中
    }
     * @api { POST } /rest/v2/strategies/fetch_item_status/ FetchItemStatus
     * @apiName FetchItemStatus
     * @apiGroup strategies
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String[]} metric_ids 指标ID
     *
     *
    */
    fetchItemStatus: RestListAPI('POST', 'rest/v2/strategies/fetch_item_status/'),
    
  },

  service_classify: {
    
    /**
     * @apiDescription 分类管理页面的服务分类列表
     * @api { GET } /rest/v2/service_classify/service_category_list/ ServiceCategoryList
     * @apiName ServiceCategoryList
     * @apiGroup service_classify
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    serviceCategoryList: RestListAPI('GET', 'rest/v2/service_classify/service_category_list/'),
    
  },

  shield: {
    
    /**
     * @apiDescription 告警屏蔽列表（通用）
     * @api { POST } /rest/v2/shield/shield_list/ ShieldList
     * @apiName ShieldList
     * @apiGroup shield
     * @apiParam {Integer} [bk_biz_id] 业务ID
     * @apiParam {Boolean} [is_active=True] 是否处于屏蔽中
     * @apiParam {String="-id","id","begin_time","-begin_time","failure_time","-failure_time"} [order=-id] 排序字段
     * @apiParam {String[]} [categories=[]] 屏蔽类型
     * @apiParam {String} [time_range] 时间范围
     * @apiParam {Integer} [page] 页码
     * @apiParam {Integer} [page_size] 每页条数
     *
     *
    */
    shieldList: RestListAPI('POST', 'rest/v2/shield/shield_list/'),
    
    /**
     * @apiDescription 告警屏蔽列表（前端）
     * @api { POST } /rest/v2/shield/frontend_shield_list/ FrontendShieldList
     * @apiName FrontendShieldList
     * @apiGroup shield
     * @apiParam {Integer} [bk_biz_id] 业务ID
     * @apiParam {Boolean} [is_active=True] 是否处于屏蔽中
     * @apiParam {String="-id","id","begin_time","-begin_time","failure_time","-failure_time"} [order=-id] 排序字段
     * @apiParam {String[]} [categories=[]] 屏蔽类型
     * @apiParam {String} [time_range] 时间范围
     * @apiParam {Integer} [page] 页码
     * @apiParam {Integer} [page_size] 每页条数
     * @apiParam {String} [search] 查询参数
     *
     *
    */
    frontendShieldList: RestListAPI('POST', 'rest/v2/shield/frontend_shield_list/'),
    
    /**
     * @apiDescription 告警屏蔽详情（通用）
     * @api { GET } /rest/v2/shield/shield_detail/ ShieldDetail
     * @apiName ShieldDetail
     * @apiGroup shield
     * @apiParam {Integer} id 屏蔽id
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    shieldDetail: RestListAPI('GET', 'rest/v2/shield/shield_detail/'),
    
    /**
     * @apiDescription 告警屏蔽详情（前端）
     * @api { GET } /rest/v2/shield/frontend_shield_detail/ FrontendShieldDetail
     * @apiName FrontendShieldDetail
     * @apiGroup shield
     * @apiParam {Integer} id 屏蔽id
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    frontendShieldDetail: RestListAPI('GET', 'rest/v2/shield/frontend_shield_detail/'),
    
    /**
     * @apiDescription 告警屏蔽详情（快照）
     * @api { POST } /rest/v2/shield/shield_snapshot/ ShieldSnapshot
     * @apiName ShieldSnapshot
     * @apiGroup shield
     * @apiParam {String} config 屏蔽快照
     *
     *
    */
    shieldSnapshot: RestListAPI('POST', 'rest/v2/shield/shield_snapshot/'),
    
    /**
     * @apiDescription 新增屏蔽（通用）
     * @api { POST } /rest/v2/shield/add_shield/ AddShield
     * @apiName AddShield
     * @apiGroup shield
     *
     *
    */
    addShield: RestListAPI('POST', 'rest/v2/shield/add_shield/'),
    
    /**
     * @apiDescription 编辑屏蔽（通用）
     * @api { POST } /rest/v2/shield/edit_shield/ EditShield
     * @apiName EditShield
     * @apiGroup shield
     * @apiParam {Integer} id 屏蔽id
     * @apiParam {Integer} bk_biz_id 业务id
     * @apiParam {String} begin_time 屏蔽开始时间
     * @apiParam {String} end_time 屏蔽结束时间
     * @apiParam {String[]} [level] 策略的屏蔽等级
     * @apiParam {String} cycle_config 周期配置
     * @apiParam {Boolean} shield_notice 是否有屏蔽通知
     * @apiParam {String} [notice_config] 通知配置
     * @apiParam {String} [description] 屏蔽原因
     *
     *
    */
    editShield: RestListAPI('POST', 'rest/v2/shield/edit_shield/'),
    
    /**
     * @apiDescription 解除屏蔽（通用）
     * @api { POST } /rest/v2/shield/disable_shield/ DisableShield
     * @apiName DisableShield
     * @apiGroup shield
     * @apiParam {Integer} id 屏蔽id
     *
     *
    */
    disableShield: RestListAPI('POST', 'rest/v2/shield/disable_shield/'),
    
    /**
     * @apiDescription 更新失效屏蔽的内容
     * @api { GET } /rest/v2/shield/update_failure_shield_content/ UpdateFailureShieldContent
     * @apiName UpdateFailureShieldContent
     * @apiGroup shield
     *
     *
    */
    updateFailureShieldContent: RestListAPI('GET', 'rest/v2/shield/update_failure_shield_content/'),
    
  },

  alert_events: {
    
    /**
     * @apiDescription 事件列表
     * @api { POST } /rest/v2/event_center/list_event/ ListEvent
     * @apiName ListEvent
     * @apiGroup alert_events
     * @apiParam {String[]} bk_biz_ids 业务id列表
     * @apiParam {String} [time_range] 时间范围
     * @apiParam {String} [receiver] 通知接受人
     * @apiParam {String="ABNORMAL","SHIELD_ABNORMAL"} [status] 事件状态
     * @apiParam {String[]} [conditions=[]] 搜索条件
     * @apiParam {Integer} [page_size=10] 获取的条数
     * @apiParam {Integer} [page=1] 页数
     * @apiParam {String} [order=None] 排序
     * @apiParam {Boolean} [export=None] 导出事件
     *
     *
    */
    listEvent: RestListAPI('POST', 'rest/v2/event_center/list_event/'),
    
    /**
     * 
     * @api { GET } /rest/v2/event_center/detail_event/ DetailEvent
     * @apiName DetailEvent
     * @apiGroup alert_events
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} id 事件ID
     *
     *
    */
    detailEvent: RestListAPI('GET', 'rest/v2/event_center/detail_event/'),
    
    /**
     * 
     * @api { GET } /rest/v2/event_center/strategy_snapshot/ StrategySnapshot
     * @apiName StrategySnapshot
     * @apiGroup alert_events
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} id 事件ID
     *
     *
    */
    strategySnapshot: RestListAPI('GET', 'rest/v2/event_center/strategy_snapshot/'),
    
    /**
     * 
     * @api { GET } /rest/v2/event_center/list_alert_notice/ ListAlertNotice
     * @apiName ListAlertNotice
     * @apiGroup alert_events
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} id 事件ID
     *
     *
    */
    listAlertNotice: RestListAPI('GET', 'rest/v2/event_center/list_alert_notice/'),
    
    /**
     * 
     * @api { GET } /rest/v2/event_center/detail_alert_notice/ DetailAlertNotice
     * @apiName DetailAlertNotice
     * @apiGroup alert_events
     * @apiParam {String} action_id 通知时间
     *
     *
    */
    detailAlertNotice: RestListAPI('GET', 'rest/v2/event_center/detail_alert_notice/'),
    
    /**
     * 
     * @api { POST } /rest/v2/event_center/ack_event/ AckEvent
     * @apiName AckEvent
     * @apiGroup alert_events
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} [id] 事件ID
     * @apiParam {String} message 确认信息
     * @apiParam {Integer[]} [ids] Ids
     *
     *
    */
    ackEvent: RestListAPI('POST', 'rest/v2/event_center/ack_event/'),
    
    /**
     * 
     * @api { POST } /rest/v2/event_center/graph_point/ GraphPoint
     * @apiName GraphPoint
     * @apiGroup alert_events
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     * @apiParam {Integer} id 事件ID
     * @apiParam {String} [time_range] 时间范围
     *
     *
    */
    graphPoint: RestListAPI('POST', 'rest/v2/event_center/graph_point/'),
    
    /**
     * @apiDescription 事件图表接口
     * @api { POST } /rest/v2/event_center/event_graph_query/ EventGraphQuery
     * @apiName EventGraphQuery
     * @apiGroup alert_events
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     * @apiParam {Integer} id 事件ID
     * @apiParam {String} data_source_label 数据来源
     * @apiParam {String} [data_type_label=time_series] 数据类型
     * @apiParam {String} metric_field 监控指标
     * @apiParam {String[]} [extend_metric_fields=[]] 监控指标列表
     * @apiParam {String} result_table_id 结果表ID
     * @apiParam {String[]} where 过滤条件
     * @apiParam {String[]} group_by 聚合字段
     * @apiParam {String} method 聚合方法
     * @apiParam {Integer} [interval=1] 时间间隔
     * @apiParam {String[]} [target=[]] 监控目标
     * @apiParam {String} [filter_dict={}] 过滤条件
     * @apiParam {Integer} [start_time] 开始时间
     * @apiParam {Integer} [end_time] 结束时间
     * @apiParam {String} [function={}] 功能函数
     *
     *
    */
    eventGraphQuery: RestListAPI('POST', 'rest/v2/event_center/event_graph_query/'),
    
    /**
     * 
     * @api { GET } /rest/v2/event_center/get_solution/ GetSolution
     * @apiName GetSolution
     * @apiGroup alert_events
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} id 事件ID
     *
     *
    */
    getSolution: RestListAPI('GET', 'rest/v2/event_center/get_solution/'),
    
    /**
     * 
     * @api { POST } /rest/v2/event_center/save_solution/ SaveSolution
     * @apiName SaveSolution
     * @apiGroup alert_events
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} id 事件ID
     * @apiParam {String} solution 解决方法
     *
     *
    */
    saveSolution: RestListAPI('POST', 'rest/v2/event_center/save_solution/'),
    
    /**
     * 
     * @api { POST } /rest/v2/event_center/event_log/ ListEventLog
     * @apiName ListEventLog
     * @apiGroup alert_events
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} id 事件ID
     * @apiParam {Integer} [offset] 上一页最后一条日志ID
     * @apiParam {Integer} [limit=10] 获取的条数
     * @apiParam {String[]} [operate=[]] 流转状态
     *
     *
    */
    listEventLog: RestListAPI('POST', 'rest/v2/event_center/event_log/'),
    
    /**
     * 
     * @api { POST } /rest/v2/event_center/list_search_item/ ListSearchItem
     * @apiName ListSearchItem
     * @apiGroup alert_events
     * @apiParam {String[]} bk_biz_ids 业务ID列表
     *
     *
    */
    listSearchItem: RestListAPI('POST', 'rest/v2/event_center/list_search_item/'),
    
    /**
     * 
     * @api { GET } /rest/v2/event_center/list_converge_log/ ListConvergeLog
     * @apiName ListConvergeLog
     * @apiGroup alert_events
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} id 事件ID
     * @apiParam {String} time_range 时间范围
     *
     *
    */
    listConvergeLog: RestListAPI('GET', 'rest/v2/event_center/list_converge_log/'),
    
    /**
     * 
     * @api { POST } /rest/v2/event_center/stacked_chart/ StackedChart
     * @apiName StackedChart
     * @apiGroup alert_events
     * @apiParam {String[]} bk_biz_ids 业务id列表
     * @apiParam {String} time_range 时间范围
     * @apiParam {String} [receiver] 通知接受人
     * @apiParam {String[]} [conditions=[]] 搜索条件
     *
     *
    */
    stackedChart: RestListAPI('POST', 'rest/v2/event_center/stacked_chart/'),
    
    /**
     * 
     * @api { GET } /rest/v2/event_center/shield_snapshot/ ShieldSnapshot
     * @apiName ShieldSnapshot
     * @apiGroup alert_events
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} id 事件ID
     * @apiParam {Integer} shield_snapshot_id 事件ID
     *
     *
    */
    shieldSnapshot: RestListAPI('GET', 'rest/v2/event_center/shield_snapshot/'),
    
    /**
     * @apiDescription 事件关联信息查询
     * @api { POST } /rest/v2/event_center/event_related_info/ EventRelatedInfo
     * @apiName EventRelatedInfo
     * @apiGroup alert_events
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer[]} ids 事件ID
     *
     *
    */
    eventRelatedInfo: RestListAPI('POST', 'rest/v2/event_center/event_related_info/'),
    
    /**
     * 
     * @api { POST } /rest/v2/event_center/list_index_by_host/ ListIndexByHost
     * @apiName ListIndexByHost
     * @apiGroup alert_events
     * @apiParam {String} ip 主机IP
     * @apiParam {Integer} [bk_cloud_id=0] 云区域ID
     * @apiParam {Integer} bk_biz_id Bk biz id
     *
     *
    */
    listIndexByHost: RestListAPI('POST', 'rest/v2/event_center/list_index_by_host/'),
    
  },

  export_import: {
    
    /**
     * @apiDescription 获取采集配置、策略配置、视图配置列表
     * @api { GET } /rest/v2/export_import/get_all_config_list/ GetAllConfigList
     * @apiName GetAllConfigList
     * @apiGroup export_import
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} [service_category_id] 服务分类
     * @apiParam {String} [label] 标签
     * @apiParam {String} [cmdb_node] 节点信息
     * @apiParam {String} [search_value] 模糊搜索字段
     *
     *
    */
    getAllConfigList: RestListAPI('GET', 'rest/v2/export_import/get_all_config_list/'),
    
    /**
     * @apiDescription 导出文件包
     * @api { POST } /rest/v2/export_import/export_package/ ExportPackage
     * @apiName ExportPackage
     * @apiGroup export_import
     *
     *
    */
    exportPackage: RestListAPI('POST', 'rest/v2/export_import/export_package/'),
    
    /**
     * @apiDescription 查看导入历史列表
     * @api { GET } /rest/v2/export_import/history_list/ HistoryList
     * @apiName HistoryList
     * @apiGroup export_import
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    historyList: RestListAPI('GET', 'rest/v2/export_import/history_list/'),
    
    /**
     * @apiDescription 查看导入历史详情
     * @api { GET } /rest/v2/export_import/history_detail/ HistoryDetail
     * @apiName HistoryDetail
     * @apiGroup export_import
     * @apiParam {Integer} import_history_id 导入历史ID
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    historyDetail: RestListAPI('GET', 'rest/v2/export_import/history_detail/'),
    
    /**
     * @apiDescription 上传文件包接口
     * @api { POST } /rest/v2/export_import/upload_package/ UploadPackage
     * @apiName UploadPackage
     * @apiGroup export_import
     * @apiParam {String} file_data 文件内容
     *
     *
    */
    uploadPackage: RestListAPI('POST', 'rest/v2/export_import/upload_package/'),
    
    /**
     * @apiDescription 导入配置接口
     * @api { POST } /rest/v2/export_import/import_config/ ImportConfig
     * @apiName ImportConfig
     * @apiGroup export_import
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String[]} uuid_list 配置的uuid
     * @apiParam {Integer} [import_history_id] 导入历史ID
     *
     *
    */
    importConfig: RestListAPI('POST', 'rest/v2/export_import/import_config/'),
    
    /**
     * 
     * @api { POST } /rest/v2/export_import/add_monitor_target/ AddMonitorTarget
     * @apiName AddMonitorTarget
     * @apiGroup export_import
     * @apiParam {Integer} import_history_id 导入历史ID
     * @apiParam {String[]} target 监控目标
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    addMonitorTarget: RestListAPI('POST', 'rest/v2/export_import/add_monitor_target/'),
    
  },

  config: {
    
    /**
     * @apiDescription 获取业务权限人员
     * @api { GET } /rest/v2/user_role/ GetUserInfo
     * @apiName GetUserInfo
     * @apiGroup config
     * @apiParam {Integer} bk_biz_id Bk biz id
     * @apiParam {Integer} [index=1] Index
     *
     *
    */
    getUserInfo: RestListAPI('GET', 'rest/v2/user_role/'),
    
    /**
     * @apiDescription 保存用户角色权限信息
     * @api { POST } /rest/v2/user_role/ SaveRolePermission
     * @apiName SaveRolePermission
     * @apiGroup config
     * @apiParam {String} role Role
     * @apiParam {String} [permission] Permission
     * @apiParam {Integer} bk_biz_id Bk biz id
     *
     * @apiSuccess {String} [create_user] 创建人
     * @apiSuccess {String} [update_user] 修改人
     * @apiSuccess {Boolean} [is_deleted] 是否删除
     * @apiSuccess {Integer} biz_id 业务ID
     * @apiSuccess {String} role 角色
     * @apiSuccess {String} [permission] 权限
     *
    */
    saveRolePermission: RestListAPI('POST', 'rest/v2/user_role/'),
    
    /**
     * @apiDescription 拉取全局配置列表
     * @api { GET } /rest/v2/global_config/ ListGlobalConfig
     * @apiName ListGlobalConfig
     * @apiGroup config
     *
     *
    */
    listGlobalConfig: RestListAPI('GET', 'rest/v2/global_config/'),
    
    /**
     * @apiDescription 设置全局配置
     * @api { POST } /rest/v2/global_config/ SetGlobalConfig
     * @apiName SetGlobalConfig
     * @apiGroup config
     * @apiParam {Object[]} configs Configs
     * @apiParam {String} configs.key Key
     * @apiParam {String} configs.value Value
     *
     *
    */
    setGlobalConfig: RestListAPI('POST', 'rest/v2/global_config/'),
    
  },

  custom_report: {
    
    /**
     * @apiDescription Proxy主机信息
     * @api { GET } /rest/v2/custom_event_report/proxy_host_info/ ProxyHostInfo
     * @apiName ProxyHostInfo
     * @apiGroup custom_report
     *
     *
    */
    proxyHostInfo: RestListAPI('GET', 'rest/v2/custom_event_report/proxy_host_info/'),
    
    /**
     * @apiDescription 自定义事件列表
     * @api { GET } /rest/v2/custom_event_report/query_custom_event_group/ QueryCustomEventGroup
     * @apiName QueryCustomEventGroup
     * @apiGroup custom_report
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     * @apiParam {String} [search_key] 名称
     * @apiParam {Integer} [page_size=10] 获取的条数
     * @apiParam {Integer} [page=1] 页数
     *
     *
    */
    queryCustomEventGroup: RestListAPI('GET', 'rest/v2/custom_event_report/query_custom_event_group/'),
    
    /**
     * @apiDescription 获取单个自定义事件详情
     * @api { GET } /rest/v2/custom_event_report/get_custom_event_group/ GetCustomEventGroup
     * @apiName GetCustomEventGroup
     * @apiGroup custom_report
     * @apiParam {Integer} bk_event_group_id 事件分组ID
     * @apiParam {String} time_range 时间范围
     *
     *
    */
    getCustomEventGroup: RestListAPI('GET', 'rest/v2/custom_event_report/get_custom_event_group/'),
    
    /**
     * @apiDescription 校验名称是否合法
     * @api { GET } /rest/v2/custom_event_report/validate_custom_event_group_name/ ValidateCustomEventGroupName
     * @apiName ValidateCustomEventGroupName
     * @apiGroup custom_report
     * @apiParam {Integer} [bk_event_group_id] Bk event group id
     * @apiParam {String} name Name
     *
     *
    */
    validateCustomEventGroupName: RestListAPI('GET', 'rest/v2/custom_event_report/validate_custom_event_group_name/'),
    
    /**
     * @apiDescription 创建自定义事件
     * @api { POST } /rest/v2/custom_event_report/create_custom_event_group/ CreateCustomEventGroup
     * @apiName CreateCustomEventGroup
     * @apiGroup custom_report
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 名称
     * @apiParam {String} scenario 对象
     * @apiParam {Object[]} [event_info_list] Event info list
     * @apiParam {Integer} [event_info_list.custom_event_id] 事件ID
     * @apiParam {String} event_info_list.custom_event_name 事件名称
     * @apiParam {Object[]} event_info_list.dimension_list Dimension list
     * @apiParam {String} event_info_list.dimension_list.dimension_name 维度字段名称
     *
     *
    */
    createCustomEventGroup: RestListAPI('POST', 'rest/v2/custom_event_report/create_custom_event_group/'),
    
    /**
     * @apiDescription 修改自定义事件
     * @api { POST } /rest/v2/custom_event_report/modify_custom_event_group/ ModifyCustomEventGroup
     * @apiName ModifyCustomEventGroup
     * @apiGroup custom_report
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} bk_event_group_id 事件分组ID
     * @apiParam {String} [name] 名称
     * @apiParam {String} [scenario] 对象
     * @apiParam {Object[]} [event_info_list] Event info list
     * @apiParam {Integer} [event_info_list.custom_event_id] 事件ID
     * @apiParam {String} event_info_list.custom_event_name 事件名称
     * @apiParam {Object[]} event_info_list.dimension_list Dimension list
     * @apiParam {String} event_info_list.dimension_list.dimension_name 维度字段名称
     * @apiParam {Boolean} [is_enable] Is enable
     *
     *
    */
    modifyCustomEventGroup: RestListAPI('POST', 'rest/v2/custom_event_report/modify_custom_event_group/'),
    
    /**
     * @apiDescription 删除自定义事件
     * @api { POST } /rest/v2/custom_event_report/delete_custom_event_group/ DeleteCustomEventGroup
     * @apiName DeleteCustomEventGroup
     * @apiGroup custom_report
     * @apiParam {Integer} bk_event_group_id 事件分组ID
     *
     *
    */
    deleteCustomEventGroup: RestListAPI('POST', 'rest/v2/custom_event_report/delete_custom_event_group/'),
    
    /**
     * @apiDescription 查询自定义时序数据最新的一条数据
     * @api { POST } /rest/v2/custom_metric_report/get_custom_time_series_latest_data_by_fields/ GetCustomTimeSeriesLatestDataByFields
     * @apiName GetCustomTimeSeriesLatestDataByFields
     * @apiGroup custom_report
     * @apiParam {String} result_table_id 结果表ID
     * @apiParam {String[]} fields_list 字段列表
     *
     *
    */
    getCustomTimeSeriesLatestDataByFields: RestListAPI('POST', 'rest/v2/custom_metric_report/get_custom_time_series_latest_data_by_fields/'),
    
    /**
     * @apiDescription 自定义时序列表
     * @api { GET } /rest/v2/custom_metric_report/custom_time_series/ CustomTimeSeriesList
     * @apiName CustomTimeSeriesList
     * @apiGroup custom_report
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     * @apiParam {String} [search_key] 名称
     * @apiParam {Integer} [page_size=10] 获取的条数
     * @apiParam {Integer} [page=1] 页数
     *
     *
    */
    customTimeSeriesList: RestListAPI('GET', 'rest/v2/custom_metric_report/custom_time_series/'),
    
    /**
     * @apiDescription 自定义时序详情
     * @api { GET } /rest/v2/custom_metric_report/custom_time_series_detail/ CustomTimeSeriesDetail
     * @apiName CustomTimeSeriesDetail
     * @apiGroup custom_report
     * @apiParam {Integer} time_series_group_id 自定义时序ID
     *
     *
    */
    customTimeSeriesDetail: RestListAPI('GET', 'rest/v2/custom_metric_report/custom_time_series_detail/'),
    
    /**
     * @apiDescription 校验名称是否合法
     * @api { GET } /rest/v2/custom_metric_report/validate_custom_ts_group_name/ ValidateCustomTsGroupName
     * @apiName ValidateCustomTsGroupName
     * @apiGroup custom_report
     * @apiParam {Integer} [time_series_group_id] Time series group id
     * @apiParam {String} name Name
     *
     *
    */
    validateCustomTsGroupName: RestListAPI('GET', 'rest/v2/custom_metric_report/validate_custom_ts_group_name/'),
    
    /**
     * @apiDescription 创建自定义时序
     * @api { POST } /rest/v2/custom_metric_report/create_custom_time_series/ CreateCustomTimeSeries
     * @apiName CreateCustomTimeSeries
     * @apiGroup custom_report
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 名称
     * @apiParam {String} scenario 对象
     * @apiParam {String} [table_id=] 表名
     * @apiParam {String[]} [metric_info_list=[]] 预定义表结构
     *
     *
    */
    createCustomTimeSeries: RestListAPI('POST', 'rest/v2/custom_metric_report/create_custom_time_series/'),
    
    /**
     * @apiDescription 修改自定义时序
     * @api { POST } /rest/v2/custom_metric_report/modify_custom_time_series/ ModifyCustomTimeSeries
     * @apiName ModifyCustomTimeSeries
     * @apiGroup custom_report
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} time_series_group_id 自定义时序ID
     * @apiParam {String} [name] 名称
     * @apiParam {Object[]} [metric_json=[]] 指标配置
     * @apiParam {Object[]} metric_json.fields 字段信息
     * @apiParam {String} metric_json.fields.unit 字段单位
     * @apiParam {String} metric_json.fields.name 字段名
     * @apiParam {String} metric_json.fields.description 字段描述
     * @apiParam {String} metric_json.fields.monitor_type 字段类型，指标或维度
     * @apiParam {String} metric_json.fields.type 字段类型
     * @apiParam {String} [metric_json.fields.label] 分组标签
     *
     *
    */
    modifyCustomTimeSeries: RestListAPI('POST', 'rest/v2/custom_metric_report/modify_custom_time_series/'),
    
    /**
     * @apiDescription 删除自定义时序
     * @api { POST } /rest/v2/custom_metric_report/delete_custom_time_series/ DeleteCustomTimeSeries
     * @apiName DeleteCustomTimeSeries
     * @apiGroup custom_report
     * @apiParam {Integer} time_series_group_id 自定义时序ID
     *
     *
    */
    deleteCustomTimeSeries: RestListAPI('POST', 'rest/v2/custom_metric_report/delete_custom_time_series/'),
    
    /**
     * 
     * @api { POST } /rest/v2/custom_metric_report/custom_time_series_graph_point/ CustomTimeSeriesGraphPoint
     * @apiName CustomTimeSeriesGraphPoint
     * @apiGroup custom_report
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} metric 指标名
     * @apiParam {Integer} time_series_group_id 自定义时序ID
     * @apiParam {String="SUM","AVG","MAX","MIN"} method 聚合方法
     * @apiParam {String} time_range 时间范围
     * @apiParam {String[]} target 目标信息
     * @apiParam {String[]} [dimensions] 维度信息
     * @apiParam {String} [unit] 单位
     *
     *
    */
    customTimeSeriesGraphPoint: RestListAPI('POST', 'rest/v2/custom_metric_report/custom_time_series_graph_point/'),
    
    /**
     * @apiDescription 自定义指标图表配置
     * @api { POST } /rest/v2/custom_metric_report/get_custom_report_dashboard_config/ GetCustomReportDashboardConfig
     * @apiName GetCustomReportDashboardConfig
     * @apiGroup custom_report
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} id 采集ID
     * @apiParam {String} [compare_config=<function GetCustomReportDashboardConfigResource.RequestSerializer.<lambda> at 0x7fd9f8338510>] 对比配置
     * @apiParam {String="leaf_node","topo_node","overview"} [view_type=leaf_node] 视图类型
     *
     *
    */
    getCustomReportDashboardConfig: RestListAPI('POST', 'rest/v2/custom_metric_report/get_custom_report_dashboard_config/'),
    
  },

  upgrade: {
    
    /**
     * @apiDescription 获取待升级项目列表
     * @api { GET } /rest/v2/upgrade/list_upgrade_items/ ListUpgradeItems
     * @apiName ListUpgradeItems
     * @apiGroup upgrade
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     *
     *
    */
    listUpgradeItems: RestListAPI('GET', 'rest/v2/upgrade/list_upgrade_items/'),
    
    /**
     * @apiDescription 执行升级
     * @api { POST } /rest/v2/upgrade/execute_upgrade/ ExecuteUpgrade
     * @apiName ExecuteUpgrade
     * @apiGroup upgrade
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     *
     *
    */
    executeUpgrade: RestListAPI('POST', 'rest/v2/upgrade/execute_upgrade/'),
    
    /**
     * @apiDescription 导出老配置为新版插件
     * @api { POST } /rest/v2/upgrade/export_collector_as_plugin/ ExportCollectorAsPlugin
     * @apiName ExportCollectorAsPlugin
     * @apiGroup upgrade
     * @apiParam {Integer} config_id 配置ID
     * @apiParam {String="script","exporter"} config_type Config type
     *
     *
    */
    exportCollectorAsPlugin: RestListAPI('POST', 'rest/v2/upgrade/export_collector_as_plugin/'),
    
    /**
     * @apiDescription 创建内置策略
     * @api { POST } /rest/v2/upgrade/create_build_in_strategy/ CreateBuildInStrategy
     * @apiName CreateBuildInStrategy
     * @apiGroup upgrade
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    createBuildInStrategy: RestListAPI('POST', 'rest/v2/upgrade/create_build_in_strategy/'),
    
    /**
     * @apiDescription 停用所有老版本策略
     * @api { POST } /rest/v2/upgrade/disable_old_strategy/ DisableOldStrategy
     * @apiName DisableOldStrategy
     * @apiGroup upgrade
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Boolean} [is_enabled=False] 是否停用
     *
     *
    */
    disableOldStrategy: RestListAPI('POST', 'rest/v2/upgrade/disable_old_strategy/'),
    
    /**
     * 
     * @api { POST } /rest/v2/upgrade/migrate_strategy/ MigrateStrategy
     * @apiName MigrateStrategy
     * @apiGroup upgrade
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer[]} item_ids 策略项ID
     * @apiParam {Integer[]} [monitor_source_ids=[]] 监控源ID
     *
     *
    */
    migrateStrategy: RestListAPI('POST', 'rest/v2/upgrade/migrate_strategy/'),
    
  },

  grafana: {
    
    /**
     * @apiDescription Grafana数据源测试接口
     * @api { GET } /rest/v2/grafana/ Test
     * @apiName Test
     * @apiGroup grafana
     *
     *
    */
    test: RestListAPI('GET', 'rest/v2/grafana/'),
    
    /**
     * @apiDescription 列出结果表的分类标签
     * @api { GET } /rest/v2/grafana/get_label/ GetLabel
     * @apiName GetLabel
     * @apiGroup grafana
     * @apiParam {String} [label_type=result_table_label] 标签类别
     * @apiParam {Integer} [level] 标签层级
     * @apiParam {Boolean} [include_admin_only=True] 是否展示管理员标签
     *
     *
    */
    getLabel: RestListAPI('GET', 'rest/v2/grafana/get_label/'),
    
    /**
     * 
     * @api { GET } /rest/v2/grafana/topo_tree/ GetTopoTree
     * @apiName GetTopoTree
     * @apiGroup grafana
     * @apiParam {Integer} bk_biz_id 业务id
     * @apiParam {String="host","service"} [instance_type] 实例类型
     * @apiParam {Boolean} [remove_empty_nodes=False] 是否删除空节点
     *
     *
    */
    getTopoTree: RestListAPI('GET', 'rest/v2/grafana/topo_tree/'),
    
    /**
     * @apiDescription 获取指标维度最近上报的值
     * @api { GET } /rest/v2/grafana/get_dimension_values/ GetDimensionValues
     * @apiName GetDimensionValues
     * @apiGroup grafana
     * @apiParam {String} result_table_id 结果表名
     * @apiParam {String} metric_field 指标名
     * @apiParam {String} field 维度名
     * @apiParam {Integer} [bk_biz_id=0] 业务ID
     * @apiParam {String} [filter_dict={}] 过滤条件
     * @apiParam {String[]} [where=[]] 查询条件
     *
     *
    */
    getDimensionValues: RestListAPI('GET', 'rest/v2/grafana/get_dimension_values/'),
    
    /**
     * @apiDescription Grafana 变量值查询
     * @api { POST } /rest/v2/grafana/get_variable_value/ GetVariableValue
     * @apiName GetVariableValue
     * @apiGroup grafana
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} type 查询类型
     * @apiParam {String} params 查询参数
     *
     *
    */
    getVariableValue: RestListAPI('POST', 'rest/v2/grafana/get_variable_value/'),
    
    /**
     * 
     * @api { GET } /rest/v2/grafana/get_variable_field/ GetVariableField
     * @apiName GetVariableField
     * @apiGroup grafana
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} type 查询类型
     *
     *
    */
    getVariableField: RestListAPI('GET', 'rest/v2/grafana/get_variable_field/'),
    
    /**
     * @apiDescription 时序数据查询
     * @api { POST } /rest/v2/grafana/time_series/query/ TimeSeriesQuery
     * @apiName TimeSeriesQuery
     * @apiGroup grafana
     * @apiParam {String} [data_format=time_series] 数据格式
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} data_source_label 数据来源
     * @apiParam {String} [data_type_label=time_series] 数据类型
     * @apiParam {String} metric_field 监控指标
     * @apiParam {String[]} [extend_metric_fields=[]] 监控指标列表
     * @apiParam {String} result_table_id 结果表ID
     * @apiParam {String[]} where 过滤条件
     * @apiParam {String[]} group_by 聚合字段
     * @apiParam {String} method 聚合方法
     * @apiParam {Integer} [interval=1] 时间间隔
     * @apiParam {String[]} [target=[]] 监控目标
     * @apiParam {String} [filter_dict={}] 过滤条件
     * @apiParam {String} [query_string=] Query string
     * @apiParam {Integer} [start_time] 开始时间
     * @apiParam {Integer} [end_time] 结束时间
     * @apiParam {String} [function={}] 功能函数
     * @apiParam {Integer} [slimit] SLIMIT
     *
     *
    */
    timeSeriesQuery: RestListAPI('POST', 'rest/v2/grafana/time_series/query/'),
    
    /**
     * @apiDescription 时序型指标
     * @api { POST } /rest/v2/grafana/time_series/metric/ TimeSeriesMetric
     * @apiName TimeSeriesMetric
     * @apiGroup grafana
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} [result_table_label=] 监控对象
     * @apiParam {String} [conditions={}] 查询条件
     *
     *
    */
    timeSeriesMetric: RestListAPI('POST', 'rest/v2/grafana/time_series/metric/'),
    
    /**
     * @apiDescription 日志数据查询
     * @api { POST } /rest/v2/grafana/log/query/ LogQuery
     * @apiName LogQuery
     * @apiGroup grafana
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} data_source_label 数据来源
     * @apiParam {String} data_type_label 数据类型
     * @apiParam {String} [query_string=] Query string
     * @apiParam {String} index_set_id 结果表ID
     * @apiParam {String[]} [where=<function LogQueryResource.RequestSerializer.<lambda> at 0x7fd9f854ff28>] 过滤条件
     * @apiParam {String} [filter_dict=<function LogQueryResource.RequestSerializer.<lambda> at 0x7fd9f81ad048>] Filter dict
     * @apiParam {Integer} [start_time] 开始时间
     * @apiParam {Integer} [end_time] 结束时间
     * @apiParam {Integer} [limit=10] 查询条数
     *
     *
    */
    logQuery: RestListAPI('POST', 'rest/v2/grafana/log/query/'),
    
    /**
     * @apiDescription 查询仪表盘列表
     * @api { GET } /rest/v2/grafana/dashboards/ GetDashboardList
     * @apiName GetDashboardList
     * @apiGroup grafana
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Boolean} [is_report=False] 是否订阅报表请求接口
     *
     *
    */
    getDashboardList: RestListAPI('GET', 'rest/v2/grafana/dashboards/'),
    
    /**
     * @apiDescription 设置默认仪表盘
     * @api { POST } /rest/v2/grafana/set_default_dashboard/ SetDefaultDashboard
     * @apiName SetDefaultDashboard
     * @apiGroup grafana
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} dashboard_uid 仪表盘ID
     *
     *
    */
    setDefaultDashboard: RestListAPI('POST', 'rest/v2/grafana/set_default_dashboard/'),
    
    /**
     * @apiDescription 查询当前默认仪表盘
     * @api { GET } /rest/v2/grafana/get_default_dashboard/ GetDefaultDashboard
     * @apiName GetDefaultDashboard
     * @apiGroup grafana
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    getDefaultDashboard: RestListAPI('GET', 'rest/v2/grafana/get_default_dashboard/'),
    
    /**
     * @apiDescription 迁移旧版仪表盘
     * @api { POST } /rest/v2/grafana/migrate_old_dashboard/ MigrateOldDashboard
     * @apiName MigrateOldDashboard
     * @apiGroup grafana
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Boolean} [only_show_config=False] 只显示新配置但不创建
     *
     *
    */
    migrateOldDashboard: RestListAPI('POST', 'rest/v2/grafana/migrate_old_dashboard/'),
    
    /**
     * @apiDescription 老仪表盘列表
     * @api { GET } /rest/v2/grafana/get_old_dashboards/ GetOldDashboards
     * @apiName GetOldDashboards
     * @apiGroup grafana
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    getOldDashboards: RestListAPI('GET', 'rest/v2/grafana/get_old_dashboards/'),
    
    /**
     * @apiDescription 查询目录树
     * @api { GET } /rest/v2/grafana/get_directory_tree/ GetDirectoryTree
     * @apiName GetDirectoryTree
     * @apiGroup grafana
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    getDirectoryTree: RestListAPI('GET', 'rest/v2/grafana/get_directory_tree/'),
    
    /**
     * 
     * @api { POST } /rest/v2/grafana/create_dashboard_or_folder/ CreateDashboardOrFolder
     * @apiName CreateDashboardOrFolder
     * @apiGroup grafana
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} title 名称
     * @apiParam {String="dashboard","folder"} type 类型
     * @apiParam {Integer} [folderId=0] 文件夹ID
     *
     *
    */
    createDashboardOrFolder: RestListAPI('POST', 'rest/v2/grafana/create_dashboard_or_folder/'),
    
    /**
     * 
     * @api { POST } /rest/v2/grafana/save_to_dashboard/ SaveToDashboard
     * @apiName SaveToDashboard
     * @apiGroup grafana
     * @apiParam {Integer} bk_biz_id Bk biz id
     * @apiParam {Object[]} panels Panels
     * @apiParam {String} panels.name 图表名称
     * @apiParam {Object[]} panels.queries 查询配合
     * @apiParam {String} panels.queries.metric_field Metric field
     * @apiParam {String} panels.queries.method Method
     * @apiParam {Integer} panels.queries.interval Interval
     * @apiParam {String} panels.queries.result_table_id Result table id
     * @apiParam {String} panels.queries.data_source_label Data source label
     * @apiParam {String} panels.queries.data_type_label Data type label
     * @apiParam {String[]} panels.queries.group_by Group by
     * @apiParam {String[]} panels.queries.where Where
     * @apiParam {String} [panels.queries.alias=] Alias
     * @apiParam {String} [panels.queries.function=<class 'dict'>] Function
     * @apiParam {Boolean} [panels.fill=False] Fill
     * @apiParam {Boolean} [panels.min_y_zero=False] Min y zero
     * @apiParam {String[]} dashboard_uids Dashboard uids
     *
     *
    */
    saveToDashboard: RestListAPI('POST', 'rest/v2/grafana/save_to_dashboard/'),
    
  },

  function_switch: {
    
    /**
     * @apiDescription 获取功能列表
     * @api { GET } /rest/v2/function_switch/ ListFunction
     * @apiName ListFunction
     * @apiGroup function_switch
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    listFunction: RestListAPI('GET', 'rest/v2/function_switch/'),
    
    /**
     * @apiDescription 开关切换
     * @api { POST } /rest/v2/function_switch/switch/ SwitchFunction
     * @apiName SwitchFunction
     * @apiGroup function_switch
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} id 功能ID
     * @apiParam {Boolean} is_enable 开关
     *
     *
    */
    switchFunction: RestListAPI('POST', 'rest/v2/function_switch/switch/'),
    
  },

  iam: {
    
    /**
     * @apiDescription 获取动作列表
     * @api { GET } /rest/v2/iam/get_authority_meta/ GetAuthorityMeta
     * @apiName GetAuthorityMeta
     * @apiGroup iam
     *
     *
    */
    getAuthorityMeta: RestListAPI('GET', 'rest/v2/iam/get_authority_meta/'),
    
    /**
     * @apiDescription 查询是否有权限
     * @api { POST } /rest/v2/iam/check_allowed_by_action_ids/ CheckAllowedByActionIds
     * @apiName CheckAllowedByActionIds
     * @apiGroup iam
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String[]} action_ids 动作ID列表
     *
     *
    */
    checkAllowedByActionIds: RestListAPI('POST', 'rest/v2/iam/check_allowed_by_action_ids/'),
    
    /**
     * @apiDescription 根据动作ID获取授权信息详情
     * @api { POST } /rest/v2/iam/get_authority_detail/ GetAuthorityDetail
     * @apiName GetAuthorityDetail
     * @apiGroup iam
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String[]} action_ids 动作ID
     *
     *
    */
    getAuthorityDetail: RestListAPI('POST', 'rest/v2/iam/get_authority_detail/'),
    
    /**
     * @apiDescription 测试抛出异常
     * @api { GET } /rest/v2/iam/test/ Test
     * @apiName Test
     * @apiGroup iam
     *
     *
    */
    test: RestListAPI('GET', 'rest/v2/iam/test/'),
    
  },

  data_explorer: {
    
    /**
     * 
     * @api { POST } /rest/v2/data_explorer/get_graph_query_config/ GetGraphQueryConfig
     * @apiName GetGraphQueryConfig
     * @apiGroup data_explorer
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Object[]} query_configs 查询配合
     * @apiParam {String} query_configs.metric_field Metric field
     * @apiParam {String} query_configs.method Method
     * @apiParam {Integer} query_configs.interval Interval
     * @apiParam {String} query_configs.result_table_id Result table id
     * @apiParam {String} query_configs.data_source_label Data source label
     * @apiParam {String} query_configs.data_type_label Data type label
     * @apiParam {String[]} query_configs.group_by Group by
     * @apiParam {String[]} query_configs.where Where
     * @apiParam {String[]} target 监控目标
     * @apiParam {Integer} start_time 开始时间
     * @apiParam {Integer} end_time 结束时间
     * @apiParam {String} compare_config 对比配置
     *
     *
    */
    getGraphQueryConfig: RestListAPI('POST', 'rest/v2/data_explorer/get_graph_query_config/'),
    
    /**
     * 
     * @api { POST } /rest/v2/data_explorer/save_panel_order/ SavePanelOrder
     * @apiName SavePanelOrder
     * @apiGroup data_explorer
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String[]} order 排序配置
     * @apiParam {String} id 配置ID
     *
     *
    */
    savePanelOrder: RestListAPI('POST', 'rest/v2/data_explorer/save_panel_order/'),
    
    /**
     * 
     * @api { POST } /rest/v2/data_explorer/delete_panel_order/ DeletePanelOrder
     * @apiName DeletePanelOrder
     * @apiGroup data_explorer
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} id 配置ID
     *
     *
    */
    deletePanelOrder: RestListAPI('POST', 'rest/v2/data_explorer/delete_panel_order/'),
    
  },

  report: {
    
    /**
     * @apiDescription 已订阅列表接口
     * @api { GET } /rest/v2/report/report_list/ ReportList
     * @apiName ReportList
     * @apiGroup report
     * @apiParam {Integer} [id] Id
     *
     *
    */
    reportList: RestListAPI('GET', 'rest/v2/report/report_list/'),
    
    /**
     * @apiDescription 已发送列表接口
     * @api { GET } /rest/v2/report/status_list/ StatusList
     * @apiName StatusList
     * @apiGroup report
     * @apiParam {Integer} [id] Id
     *
     *
    */
    statusList: RestListAPI('GET', 'rest/v2/report/status_list/'),
    
    /**
     * @apiDescription 每个业务下的图表列表接口
     * @api { GET } /rest/v2/report/graphs_list_by_biz/ GraphsListByBiz
     * @apiName GraphsListByBiz
     * @apiGroup report
     * @apiParam {Integer} bk_biz_id Bk biz id
     *
     *
    */
    graphsListByBiz: RestListAPI('GET', 'rest/v2/report/graphs_list_by_biz/'),
    
    /**
     * @apiDescription 创建/编辑订阅报表
     * @api { POST } /rest/v2/report/report_create_or_update/ ReportCreateOrUpdate
     * @apiName ReportCreateOrUpdate
     * @apiGroup report
     * @apiParam {Integer} [report_item_id] Report item id
     * @apiParam {String} [mail_title] Mail title
     * @apiParam {Object[]} [receivers] Receivers
     * @apiParam {String} receivers.id 用户名或组ID
     * @apiParam {String} [receivers.name] 用户名或组名
     * @apiParam {String="bk_biz_maintainer","bk_biz_productor","bk_biz_developer","bk_biz_tester","bk_biz_controller","bk_biz_notify_receiver",""} [receivers.group] 所属组别
     * @apiParam {String="user","group"} receivers.type Type
     * @apiParam {Boolean} receivers.is_enabled 是否启动订阅
     * @apiParam {Object[]} [managers] Managers
     * @apiParam {String} managers.id 用户名或组ID
     * @apiParam {String} [managers.name] 用户名或组名
     * @apiParam {String="bk_biz_maintainer","bk_biz_productor","bk_biz_developer","bk_biz_tester","bk_biz_controller","bk_biz_notify_receiver",""} [managers.group] 所属组别
     * @apiParam {String="user","group"} managers.type Type
     * @apiParam {Object} [frequency] Frequency
     * @apiParam {Integer} frequency.type 频率类型
     * @apiParam {String[]} frequency.day_list 几天
     * @apiParam {String[]} frequency.week_list 周几
     * @apiParam {String} frequency.run_time 运行时间
     * @apiParam {Object[]} [report_contents] Report contents
     * @apiParam {String} report_contents.content_title 子内容标题
     * @apiParam {String} report_contents.content_details 字内容说明
     * @apiParam {Integer} report_contents.row_pictures_num 一行几幅图
     * @apiParam {String[]} report_contents.graphs 图表
     * @apiParam {Boolean} [is_enabled] Is enabled
     *
     *
    */
    reportCreateOrUpdate: RestListAPI('POST', 'rest/v2/report/report_create_or_update/'),
    
    /**
     * @apiDescription 测试订阅报表
     * @api { POST } /rest/v2/report/report_test/ ReportTest
     * @apiName ReportTest
     * @apiGroup report
     * @apiParam {String} mail_title Mail title
     * @apiParam {Object[]} receivers Receivers
     * @apiParam {String} receivers.id 用户名或组ID
     * @apiParam {String} [receivers.name] 用户名或组名
     * @apiParam {String="bk_biz_maintainer","bk_biz_productor","bk_biz_developer","bk_biz_tester","bk_biz_controller","bk_biz_notify_receiver",""} [receivers.group] 所属组别
     * @apiParam {String="user","group"} receivers.type Type
     * @apiParam {Boolean} receivers.is_enabled 是否启动订阅
     * @apiParam {Object[]} report_contents Report contents
     * @apiParam {String} report_contents.content_title 子内容标题
     * @apiParam {String} report_contents.content_details 字内容说明
     * @apiParam {Integer} report_contents.row_pictures_num 一行几幅图
     * @apiParam {String[]} report_contents.graphs 图表
     * @apiParam {Object} [frequency] Frequency
     * @apiParam {Integer} frequency.type 频率类型
     * @apiParam {String[]} frequency.day_list 几天
     * @apiParam {String[]} frequency.week_list 周几
     * @apiParam {String} frequency.run_time 运行时间
     *
     *
    */
    reportTest: RestListAPI('POST', 'rest/v2/report/report_test/'),
    
    /**
     * @apiDescription 内置指标
     * @api { GET } /rest/v2/report/build_in_metric/ BuildInMetric
     * @apiName BuildInMetric
     * @apiGroup report
     *
     *
    */
    buildInMetric: RestListAPI('GET', 'rest/v2/report/build_in_metric/'),
    
    /**
     * @apiDescription 订阅内容获取接口
     * @api { GET } /rest/v2/report/report_content/ ReportContent
     * @apiName ReportContent
     * @apiGroup report
     * @apiParam {Integer} report_item_id Report item id
     *
     *
    */
    reportContent: RestListAPI('GET', 'rest/v2/report/report_content/'),
    
    /**
     * @apiDescription 删除订阅报表
     * @api { POST } /rest/v2/report/report_delete/ ReportDelete
     * @apiName ReportDelete
     * @apiGroup report
     * @apiParam {Integer} report_item_id Report item id
     *
     *
    */
    reportDelete: RestListAPI('POST', 'rest/v2/report/report_delete/'),
    
    /**
     * @apiDescription 订阅报表用户组列表接口
     * @api { GET } /rest/v2/report/group_list/ GroupList
     * @apiName GroupList
     * @apiGroup report
     *
     *
    */
    groupList: RestListAPI('GET', 'rest/v2/report/group_list/'),
    
    /**
     * @apiDescription 订阅报表克隆接口
     * @api { GET } /rest/v2/report/report_clone/ ReportClone
     * @apiName ReportClone
     * @apiGroup report
     * @apiParam {Integer} report_item_id Report item id
     *
     *
    */
    reportClone: RestListAPI('GET', 'rest/v2/report/report_clone/'),
    
  },

  mobile_event: {
    
    /**
     * @apiDescription 根据汇总ID展示告警信息及事件列表
     * @api { GET } /weixin/rest/v1/event/get_alarm_detail/ GetAlarmDetail
     * @apiName GetAlarmDetail
     * @apiGroup mobile_event
     * @apiParam {Integer} alert_collect_id Alert collect id
     * @apiParam {Integer} bk_biz_id Bk biz id
     *
     *
    */
    getAlarmDetail: RestListAPI('GET', 'weixin/rest/v1/event/get_alarm_detail/'),
    
    /**
     * @apiDescription 事件详情
     * @api { GET } /weixin/rest/v1/event/get_event_detail/ GetEventDetail
     * @apiName GetEventDetail
     * @apiGroup mobile_event
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} event_id 事件ID
     *
     *
    */
    getEventDetail: RestListAPI('GET', 'weixin/rest/v1/event/get_event_detail/'),
    
    /**
     * @apiDescription 查询事件视图
     * @api { GET } /weixin/rest/v1/event/get_event_graph_view/ GetEventGraphView
     * @apiName GetEventGraphView
     * @apiGroup mobile_event
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {Integer} event_id 事件ID
     * @apiParam {Integer} [start_time] 开始时间
     * @apiParam {Integer} [end_time] 结束时间
     * @apiParam {Integer} [time_compare] 时间对比(小时)
     *
     *
    */
    getEventGraphView: RestListAPI('GET', 'weixin/rest/v1/event/get_event_graph_view/'),
    
    /**
     * @apiDescription 快速屏蔽事件
     * @api { POST } /weixin/rest/v1/event/quick_shield/ QuickShield
     * @apiName QuickShield
     * @apiGroup mobile_event
     * @apiParam {String="scope","strategy","event"} type 屏蔽类型
     * @apiParam {Integer} event_id 事件ID
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} end_time 屏蔽结束时间
     * @apiParam {String} [description=] 屏蔽描述
     *
     *
    */
    quickShield: RestListAPI('POST', 'weixin/rest/v1/event/quick_shield/'),
    
    /**
     * @apiDescription 获取未恢复事件列表
     * @api { GET } /weixin/rest/v1/event/get_event_list/ GetEventList
     * @apiName GetEventList
     * @apiGroup mobile_event
     * @apiParam {Integer} [level] 告警级别
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String="strategy","target","shield"} [type=strategy] 分组类型
     * @apiParam {Boolean} [only_count=False] 只看统计数量
     *
     *
    */
    getEventList: RestListAPI('GET', 'weixin/rest/v1/event/get_event_list/'),
    
    /**
     * @apiDescription 基于告警汇总对事件进行批量确认
     * @api { POST } /weixin/rest/v1/event/ack_event/ AckEvent
     * @apiName AckEvent
     * @apiGroup mobile_event
     * @apiParam {Integer} alert_collect_id 告警汇总ID
     * @apiParam {Integer} bk_biz_id 业务ID
     *
     *
    */
    ackEvent: RestListAPI('POST', 'weixin/rest/v1/event/ack_event/'),
    
  },

}


/* Model API */
const Model = {

  readOnlyModel: {
    
    /**
     * 
     * @api { GET } /rest/v1/read_only_model/count/ Count
     * @apiName Count
     * @apiGroup readOnlyModel
     *
    */
    count: RestListAPI('GET', 'rest/v1/read_only_model/count/'),
    
    /**
     * 
     * @api { GET } /rest/v1/read_only_model/ List
     * @apiName List
     * @apiGroup readOnlyModel
     *
    */
    list: RestListAPI('GET', 'rest/v1/read_only_model/'),
    
    /**
     * 
     * @api { GET } /rest/v1/read_only_model/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup readOnlyModel
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v1/read_only_model/{pk}/'),
    
  },

  model: {
    
    /**
     * 
     * @api { GET } /rest/v1/model/count/ Count
     * @apiName Count
     * @apiGroup model
     *
    */
    count: RestListAPI('GET', 'rest/v1/model/count/'),
    
    /**
     * 
     * @api { POST } /rest/v1/model/ Create
     * @apiName Create
     * @apiGroup model
     *
    */
    create: RestListAPI('POST', 'rest/v1/model/'),
    
    /**
     * 
     * @api { DELETE } /rest/v1/model/{pk}/ Destroy
     * @apiName Destroy
     * @apiGroup model
     *
    */
    destroy: RestDetailAPI('DELETE', 'rest/v1/model/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v1/model/ List
     * @apiName List
     * @apiGroup model
     *
    */
    list: RestListAPI('GET', 'rest/v1/model/'),
    
    /**
     * 
     * @api { PATCH } /rest/v1/model/{pk}/ PartialUpdate
     * @apiName PartialUpdate
     * @apiGroup model
     *
    */
    partialUpdate: RestDetailAPI('PATCH', 'rest/v1/model/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v1/model/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup model
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v1/model/{pk}/'),
    
    /**
     * 
     * @api { PUT } /rest/v1/model/{pk}/ Update
     * @apiName Update
     * @apiGroup model
     *
    */
    update: RestDetailAPI('PUT', 'rest/v1/model/{pk}/'),
    
  },

  baseAlarm: {
    
    /**
     * 
     * @api { GET } /rest/v1/base_alarm/count/ Count
     * @apiName Count
     * @apiGroup baseAlarm
     * @apiParam {Integer} [alarm_type] 告警标识
     * @apiParam {String} [title] 基础告警名称
     * @apiParam {String} [description] 基础告警描述
     * @apiParam {String} [is_enable] 是否启用
     * @apiParam {String} [dimensions] 维度
     *
    */
    count: RestListAPI('GET', 'rest/v1/base_alarm/count/'),
    
    /**
     * 
     * @api { GET } /rest/v1/base_alarm/ List
     * @apiName List
     * @apiGroup baseAlarm
     * @apiParam {Integer} [alarm_type] 告警标识
     * @apiParam {String} [title] 基础告警名称
     * @apiParam {String} [description] 基础告警描述
     * @apiParam {String} [is_enable] 是否启用
     * @apiParam {String} [dimensions] 维度
     *
    */
    list: RestListAPI('GET', 'rest/v1/base_alarm/'),
    
    /**
     * 
     * @api { GET } /rest/v1/base_alarm/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup baseAlarm
     * @apiParam {Integer} [alarm_type] 告警标识
     * @apiParam {String} [title] 基础告警名称
     * @apiParam {String} [description] 基础告警描述
     * @apiParam {String} [is_enable] 是否启用
     * @apiParam {String} [dimensions] 维度
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v1/base_alarm/{pk}/'),
    
  },

  snapshotHostIndex: {
    
    /**
     * 
     * @api { GET } /rest/v1/snapshot_host_index/count/ Count
     * @apiName Count
     * @apiGroup snapshotHostIndex
     * @apiParam {String} category Category
     * @apiParam {String} item Item
     * @apiParam {String} type Type
     * @apiParam {String} result_table_id Result table id
     * @apiParam {String} description Description
     * @apiParam {String} dimension_field Dimension field
     * @apiParam {Number} conversion Conversion
     * @apiParam {String} conversion_unit Conversion unit
     * @apiParam {String} [metric] Metric
     * @apiParam {Boolean} [is_linux] Is liunx metric
     * @apiParam {Boolean} [is_windows] Is windows metric
     * @apiParam {Boolean} [is_aix] Is aix metric
     *
    */
    count: RestListAPI('GET', 'rest/v1/snapshot_host_index/count/'),
    
    /**
     * 
     * @api { GET } /rest/v1/snapshot_host_index/ List
     * @apiName List
     * @apiGroup snapshotHostIndex
     * @apiParam {String} category Category
     * @apiParam {String} item Item
     * @apiParam {String} type Type
     * @apiParam {String} result_table_id Result table id
     * @apiParam {String} description Description
     * @apiParam {String} dimension_field Dimension field
     * @apiParam {Number} conversion Conversion
     * @apiParam {String} conversion_unit Conversion unit
     * @apiParam {String} [metric] Metric
     * @apiParam {Boolean} [is_linux] Is liunx metric
     * @apiParam {Boolean} [is_windows] Is windows metric
     * @apiParam {Boolean} [is_aix] Is aix metric
     *
    */
    list: RestListAPI('GET', 'rest/v1/snapshot_host_index/'),
    
    /**
     * 
     * @api { GET } /rest/v1/snapshot_host_index/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup snapshotHostIndex
     * @apiParam {String} category Category
     * @apiParam {String} item Item
     * @apiParam {String} type Type
     * @apiParam {String} result_table_id Result table id
     * @apiParam {String} description Description
     * @apiParam {String} dimension_field Dimension field
     * @apiParam {Number} conversion Conversion
     * @apiParam {String} conversion_unit Conversion unit
     * @apiParam {String} [metric] Metric
     * @apiParam {Boolean} [is_linux] Is liunx metric
     * @apiParam {Boolean} [is_windows] Is windows metric
     * @apiParam {Boolean} [is_aix] Is aix metric
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v1/snapshot_host_index/{pk}/'),
    
  },

  rolePermission: {
    
    /**
     * 
     * @api { GET } /rest/v1/role_permission/count/ Count
     * @apiName Count
     * @apiGroup rolePermission
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} biz_id 业务ID
     * @apiParam {String} role 角色
     * @apiParam {String} [permission] 权限
     *
    */
    count: RestListAPI('GET', 'rest/v1/role_permission/count/'),
    
    /**
     * 
     * @api { POST } /rest/v1/role_permission/ Create
     * @apiName Create
     * @apiGroup rolePermission
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} biz_id 业务ID
     * @apiParam {String} role 角色
     * @apiParam {String} [permission] 权限
     *
    */
    create: RestListAPI('POST', 'rest/v1/role_permission/'),
    
    /**
     * 
     * @api { DELETE } /rest/v1/role_permission/{pk}/ Destroy
     * @apiName Destroy
     * @apiGroup rolePermission
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} biz_id 业务ID
     * @apiParam {String} role 角色
     * @apiParam {String} [permission] 权限
     *
    */
    destroy: RestDetailAPI('DELETE', 'rest/v1/role_permission/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v1/role_permission/ List
     * @apiName List
     * @apiGroup rolePermission
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} biz_id 业务ID
     * @apiParam {String} role 角色
     * @apiParam {String} [permission] 权限
     *
    */
    list: RestListAPI('GET', 'rest/v1/role_permission/'),
    
    /**
     * 
     * @api { PATCH } /rest/v1/role_permission/{pk}/ PartialUpdate
     * @apiName PartialUpdate
     * @apiGroup rolePermission
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} biz_id 业务ID
     * @apiParam {String} role 角色
     * @apiParam {String} [permission] 权限
     *
    */
    partialUpdate: RestDetailAPI('PATCH', 'rest/v1/role_permission/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v1/role_permission/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup rolePermission
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} biz_id 业务ID
     * @apiParam {String} role 角色
     * @apiParam {String} [permission] 权限
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v1/role_permission/{pk}/'),
    
    /**
     * 
     * @api { PUT } /rest/v1/role_permission/{pk}/ Update
     * @apiName Update
     * @apiGroup rolePermission
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} biz_id 业务ID
     * @apiParam {String} role 角色
     * @apiParam {String} [permission] 权限
     *
    */
    update: RestDetailAPI('PUT', 'rest/v1/role_permission/{pk}/'),
    
  },

  indexColorConf: {
    
    /**
     * 
     * @api { GET } /rest/v1/index_color_conf/count/ Count
     * @apiName Count
     * @apiGroup indexColorConf
     * @apiParam {String} range 取值区间
     * @apiParam {String} color 颜色
     * @apiParam {String} slug 方案标签
     *
    */
    count: RestListAPI('GET', 'rest/v1/index_color_conf/count/'),
    
    /**
     * 
     * @api { GET } /rest/v1/index_color_conf/ List
     * @apiName List
     * @apiGroup indexColorConf
     * @apiParam {String} range 取值区间
     * @apiParam {String} color 颜色
     * @apiParam {String} slug 方案标签
     *
    */
    list: RestListAPI('GET', 'rest/v1/index_color_conf/'),
    
    /**
     * 
     * @api { GET } /rest/v1/index_color_conf/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup indexColorConf
     * @apiParam {String} range 取值区间
     * @apiParam {String} color 颜色
     * @apiParam {String} slug 方案标签
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v1/index_color_conf/{pk}/'),
    
  },

  userConfig: {
    
    /**
     * 
     * @api { GET } /rest/v1/user_config/count/ Count
     * @apiName Count
     * @apiGroup userConfig
     * @apiParam {String} username 用户名
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    count: RestListAPI('GET', 'rest/v1/user_config/count/'),
    
    /**
     * 
     * @api { POST } /rest/v1/user_config/ Create
     * @apiName Create
     * @apiGroup userConfig
     * @apiParam {String} username 用户名
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    create: RestListAPI('POST', 'rest/v1/user_config/'),
    
    /**
     * 
     * @api { DELETE } /rest/v1/user_config/{pk}/ Destroy
     * @apiName Destroy
     * @apiGroup userConfig
     * @apiParam {String} username 用户名
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    destroy: RestDetailAPI('DELETE', 'rest/v1/user_config/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v1/user_config/ List
     * @apiName List
     * @apiGroup userConfig
     * @apiParam {String} username 用户名
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    list: RestListAPI('GET', 'rest/v1/user_config/'),
    
    /**
     * 
     * @api { PATCH } /rest/v1/user_config/{pk}/ PartialUpdate
     * @apiName PartialUpdate
     * @apiGroup userConfig
     * @apiParam {String} username 用户名
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    partialUpdate: RestDetailAPI('PATCH', 'rest/v1/user_config/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v1/user_config/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup userConfig
     * @apiParam {String} username 用户名
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v1/user_config/{pk}/'),
    
    /**
     * 
     * @api { PUT } /rest/v1/user_config/{pk}/ Update
     * @apiName Update
     * @apiGroup userConfig
     * @apiParam {String} username 用户名
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    update: RestDetailAPI('PUT', 'rest/v1/user_config/{pk}/'),
    
  },

  applicationConfig: {
    
    /**
     * 
     * @api { GET } /rest/v1/application_config/count/ Count
     * @apiName Count
     * @apiGroup applicationConfig
     * @apiParam {Integer} cc_biz_id 业务id
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    count: RestListAPI('GET', 'rest/v1/application_config/count/'),
    
    /**
     * 
     * @api { POST } /rest/v1/application_config/ Create
     * @apiName Create
     * @apiGroup applicationConfig
     * @apiParam {Integer} cc_biz_id 业务id
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    create: RestListAPI('POST', 'rest/v1/application_config/'),
    
    /**
     * 
     * @api { DELETE } /rest/v1/application_config/{pk}/ Destroy
     * @apiName Destroy
     * @apiGroup applicationConfig
     * @apiParam {Integer} cc_biz_id 业务id
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    destroy: RestDetailAPI('DELETE', 'rest/v1/application_config/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v1/application_config/ List
     * @apiName List
     * @apiGroup applicationConfig
     * @apiParam {Integer} cc_biz_id 业务id
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    list: RestListAPI('GET', 'rest/v1/application_config/'),
    
    /**
     * 
     * @api { PATCH } /rest/v1/application_config/{pk}/ PartialUpdate
     * @apiName PartialUpdate
     * @apiGroup applicationConfig
     * @apiParam {Integer} cc_biz_id 业务id
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    partialUpdate: RestDetailAPI('PATCH', 'rest/v1/application_config/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v1/application_config/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup applicationConfig
     * @apiParam {Integer} cc_biz_id 业务id
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v1/application_config/{pk}/'),
    
    /**
     * 
     * @api { PUT } /rest/v1/application_config/{pk}/ Update
     * @apiName Update
     * @apiGroup applicationConfig
     * @apiParam {Integer} cc_biz_id 业务id
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    update: RestDetailAPI('PUT', 'rest/v1/application_config/{pk}/'),
    
  },

  globalConfig: {
    
    /**
     * 
     * @api { GET } /rest/v1/global_config/count/ Count
     * @apiName Count
     * @apiGroup globalConfig
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    count: RestListAPI('GET', 'rest/v1/global_config/count/'),
    
    /**
     * 
     * @api { GET } /rest/v1/global_config/ List
     * @apiName List
     * @apiGroup globalConfig
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    list: RestListAPI('GET', 'rest/v1/global_config/'),
    
    /**
     * 
     * @api { GET } /rest/v1/global_config/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup globalConfig
     * @apiParam {String} key Key
     * @apiParam {String} value 配置信息
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v1/global_config/{pk}/'),
    
  },

  operateRecord: {
    
    /**
     * 
     * @api { GET } /rest/v1/operate_record/count/ Count
     * @apiName Count
     * @apiGroup operateRecord
     * @apiParam {Integer} [biz_id] 业务cc_id
     * @apiParam {String} config_type 配置类型
     * @apiParam {Integer} config_id 操作config_id
     * @apiParam {String} [config_title] 配置标题
     * @apiParam {String} operator 操作人
     * @apiParam {String} [operator_name] 操作人昵称
     * @apiParam {String} operate 具体操作
     * @apiParam {String} data 数据(JSON)
     * @apiParam {String} [data_ori] 修改前数据(JSON)
     * @apiParam {String} [operate_desc] 操作说明
     *
    */
    count: RestListAPI('GET', 'rest/v1/operate_record/count/'),
    
    /**
     * 
     * @api { GET } /rest/v1/operate_record/ List
     * @apiName List
     * @apiGroup operateRecord
     * @apiParam {Integer} [biz_id] 业务cc_id
     * @apiParam {String} config_type 配置类型
     * @apiParam {Integer} config_id 操作config_id
     * @apiParam {String} [config_title] 配置标题
     * @apiParam {String} operator 操作人
     * @apiParam {String} [operator_name] 操作人昵称
     * @apiParam {String} operate 具体操作
     * @apiParam {String} data 数据(JSON)
     * @apiParam {String} [data_ori] 修改前数据(JSON)
     * @apiParam {String} [operate_desc] 操作说明
     *
    */
    list: RestListAPI('GET', 'rest/v1/operate_record/'),
    
    /**
     * 
     * @api { GET } /rest/v1/operate_record/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup operateRecord
     * @apiParam {Integer} [biz_id] 业务cc_id
     * @apiParam {String} config_type 配置类型
     * @apiParam {Integer} config_id 操作config_id
     * @apiParam {String} [config_title] 配置标题
     * @apiParam {String} operator 操作人
     * @apiParam {String} [operator_name] 操作人昵称
     * @apiParam {String} operate 具体操作
     * @apiParam {String} data 数据(JSON)
     * @apiParam {String} [data_ori] 修改前数据(JSON)
     * @apiParam {String} [operate_desc] 操作说明
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v1/operate_record/{pk}/'),
    
  },

  monitorLocation: {
    
    /**
     * 
     * @api { GET } /rest/v1/monitor_location/count/ Count
     * @apiName Count
     * @apiGroup monitorLocation
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {String} biz_id 业务ID
     * @apiParam {Integer} menu_id 菜单id
     * @apiParam {Integer} monitor_id 监控id
     * @apiParam {Integer} [graph_index] 图表所在栏目位置
     * @apiParam {Integer} [width] 宽度
     *
    */
    count: RestListAPI('GET', 'rest/v1/monitor_location/count/'),
    
    /**
     * 
     * @api { POST } /rest/v1/monitor_location/ Create
     * @apiName Create
     * @apiGroup monitorLocation
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {String} biz_id 业务ID
     * @apiParam {Integer} menu_id 菜单id
     * @apiParam {Integer} monitor_id 监控id
     * @apiParam {Integer} [graph_index] 图表所在栏目位置
     * @apiParam {Integer} [width] 宽度
     *
    */
    create: RestListAPI('POST', 'rest/v1/monitor_location/'),
    
    /**
     * 
     * @api { DELETE } /rest/v1/monitor_location/{pk}/ Destroy
     * @apiName Destroy
     * @apiGroup monitorLocation
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {String} biz_id 业务ID
     * @apiParam {Integer} menu_id 菜单id
     * @apiParam {Integer} monitor_id 监控id
     * @apiParam {Integer} [graph_index] 图表所在栏目位置
     * @apiParam {Integer} [width] 宽度
     *
    */
    destroy: RestDetailAPI('DELETE', 'rest/v1/monitor_location/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v1/monitor_location/ List
     * @apiName List
     * @apiGroup monitorLocation
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {String} biz_id 业务ID
     * @apiParam {Integer} menu_id 菜单id
     * @apiParam {Integer} monitor_id 监控id
     * @apiParam {Integer} [graph_index] 图表所在栏目位置
     * @apiParam {Integer} [width] 宽度
     *
    */
    list: RestListAPI('GET', 'rest/v1/monitor_location/'),
    
    /**
     * 
     * @api { PATCH } /rest/v1/monitor_location/{pk}/ PartialUpdate
     * @apiName PartialUpdate
     * @apiGroup monitorLocation
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {String} biz_id 业务ID
     * @apiParam {Integer} menu_id 菜单id
     * @apiParam {Integer} monitor_id 监控id
     * @apiParam {Integer} [graph_index] 图表所在栏目位置
     * @apiParam {Integer} [width] 宽度
     *
    */
    partialUpdate: RestDetailAPI('PATCH', 'rest/v1/monitor_location/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v1/monitor_location/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup monitorLocation
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {String} biz_id 业务ID
     * @apiParam {Integer} menu_id 菜单id
     * @apiParam {Integer} monitor_id 监控id
     * @apiParam {Integer} [graph_index] 图表所在栏目位置
     * @apiParam {Integer} [width] 宽度
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v1/monitor_location/{pk}/'),
    
    /**
     * 
     * @api { PUT } /rest/v1/monitor_location/{pk}/ Update
     * @apiName Update
     * @apiGroup monitorLocation
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {String} biz_id 业务ID
     * @apiParam {Integer} menu_id 菜单id
     * @apiParam {Integer} monitor_id 监控id
     * @apiParam {Integer} [graph_index] 图表所在栏目位置
     * @apiParam {Integer} [width] 宽度
     *
    */
    update: RestDetailAPI('PUT', 'rest/v1/monitor_location/{pk}/'),
    
  },

  alarmType: {
    
    /**
     * 
     * @api { GET } /rest/v1/alarm_type/ List
     * @apiName List
     * @apiGroup alarmType
     *
    */
    list: RestListAPI('GET', 'rest/v1/alarm_type/'),
    
  },

  uptimeCheckNode: {
    
    /**
     * 
     * @api { GET } /rest/v2/uptime_check/uptime_check_node/count/ Count
     * @apiName Count
     * @apiGroup uptimeCheckNode
     * @apiParam {String} [location] Location
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} [bk_biz_id] 业务ID
     * @apiParam {Boolean} [is_common] 是否为通用节点
     * @apiParam {String} name 节点名称
     * @apiParam {String} ip IP地址
     * @apiParam {Integer} plat_id 云区域ID
     * @apiParam {String} [carrieroperator] Carrieroperator
     *
    */
    count: RestListAPI('GET', 'rest/v2/uptime_check/uptime_check_node/count/'),
    
    /**
     * 
     * @api { POST } /rest/v2/uptime_check/uptime_check_node/ Create
     * @apiName Create
     * @apiGroup uptimeCheckNode
     * @apiParam {String} [location] Location
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} [bk_biz_id] 业务ID
     * @apiParam {Boolean} [is_common] 是否为通用节点
     * @apiParam {String} name 节点名称
     * @apiParam {String} ip IP地址
     * @apiParam {Integer} plat_id 云区域ID
     * @apiParam {String} [carrieroperator] Carrieroperator
     *
    */
    create: RestListAPI('POST', 'rest/v2/uptime_check/uptime_check_node/'),
    
    /**
     * 
     * @api { DELETE } /rest/v2/uptime_check/uptime_check_node/{pk}/ Destroy
     * @apiName Destroy
     * @apiGroup uptimeCheckNode
     * @apiParam {String} [location] Location
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} [bk_biz_id] 业务ID
     * @apiParam {Boolean} [is_common] 是否为通用节点
     * @apiParam {String} name 节点名称
     * @apiParam {String} ip IP地址
     * @apiParam {Integer} plat_id 云区域ID
     * @apiParam {String} [carrieroperator] Carrieroperator
     *
    */
    destroy: RestDetailAPI('DELETE', 'rest/v2/uptime_check/uptime_check_node/{pk}/'),
    
    /**
     * @apiDescription 节点重名时自动补全一个名称，如广东移动补全为广东移动2
     * @api { GET } /rest/v2/uptime_check/uptime_check_node/fix_name_conflict/ FixNameConflict
     * @apiName FixNameConflict
     * @apiGroup uptimeCheckNode
     * @apiParam {String} [location] Location
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} [bk_biz_id] 业务ID
     * @apiParam {Boolean} [is_common] 是否为通用节点
     * @apiParam {String} name 节点名称
     * @apiParam {String} ip IP地址
     * @apiParam {Integer} plat_id 云区域ID
     * @apiParam {String} [carrieroperator] Carrieroperator
     *
    */
    fixNameConflict: RestListAPI('GET', 'rest/v2/uptime_check/uptime_check_node/fix_name_conflict/'),
    
    /**
     * @apiDescription 用于给前端判断输入的IP是否属于已建节点
     * @api { GET } /rest/v2/uptime_check/uptime_check_node/is_exist/ IsExist
     * @apiName IsExist
     * @apiGroup uptimeCheckNode
     * @apiParam {String} [location] Location
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} [bk_biz_id] 业务ID
     * @apiParam {Boolean} [is_common] 是否为通用节点
     * @apiParam {String} name 节点名称
     * @apiParam {String} ip IP地址
     * @apiParam {Integer} plat_id 云区域ID
     * @apiParam {String} [carrieroperator] Carrieroperator
     *
    */
    isExist: RestListAPI('GET', 'rest/v2/uptime_check/uptime_check_node/is_exist/'),
    
    /**
     * @apiDescription 重写list,简化节点部分数据并添加关联任务数等数据
     * @api { GET } /rest/v2/uptime_check/uptime_check_node/ List
     * @apiName List
     * @apiGroup uptimeCheckNode
     * @apiParam {String} [location] Location
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} [bk_biz_id] 业务ID
     * @apiParam {Boolean} [is_common] 是否为通用节点
     * @apiParam {String} name 节点名称
     * @apiParam {String} ip IP地址
     * @apiParam {Integer} plat_id 云区域ID
     * @apiParam {String} [carrieroperator] Carrieroperator
     *
    */
    list: RestListAPI('GET', 'rest/v2/uptime_check/uptime_check_node/'),
    
    /**
     * 
     * @api { PATCH } /rest/v2/uptime_check/uptime_check_node/{pk}/ PartialUpdate
     * @apiName PartialUpdate
     * @apiGroup uptimeCheckNode
     * @apiParam {String} [location] Location
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} [bk_biz_id] 业务ID
     * @apiParam {Boolean} [is_common] 是否为通用节点
     * @apiParam {String} name 节点名称
     * @apiParam {String} ip IP地址
     * @apiParam {Integer} plat_id 云区域ID
     * @apiParam {String} [carrieroperator] Carrieroperator
     *
    */
    partialUpdate: RestDetailAPI('PATCH', 'rest/v2/uptime_check/uptime_check_node/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v2/uptime_check/uptime_check_node/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup uptimeCheckNode
     * @apiParam {String} [location] Location
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} [bk_biz_id] 业务ID
     * @apiParam {Boolean} [is_common] 是否为通用节点
     * @apiParam {String} name 节点名称
     * @apiParam {String} ip IP地址
     * @apiParam {Integer} plat_id 云区域ID
     * @apiParam {String} [carrieroperator] Carrieroperator
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v2/uptime_check/uptime_check_node/{pk}/'),
    
    /**
     * 
     * @api { PUT } /rest/v2/uptime_check/uptime_check_node/{pk}/ Update
     * @apiName Update
     * @apiGroup uptimeCheckNode
     * @apiParam {String} [location] Location
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} [bk_biz_id] 业务ID
     * @apiParam {Boolean} [is_common] 是否为通用节点
     * @apiParam {String} name 节点名称
     * @apiParam {String} ip IP地址
     * @apiParam {Integer} plat_id 云区域ID
     * @apiParam {String} [carrieroperator] Carrieroperator
     *
    */
    update: RestDetailAPI('PUT', 'rest/v2/uptime_check/uptime_check_node/{pk}/'),
    
  },

  uptimeCheckTask: {
    
    /**
     * @apiDescription 更改任务状态
     * @api { POST } /rest/v2/uptime_check/uptime_check_task/{pk}/change_status/ ChangeStatus
     * @apiName ChangeStatus
     * @apiGroup uptimeCheckTask
     * @apiParam {Object} config Config
     * @apiParam {String} [config.method] Method
     * @apiParam {String} [config.urls] Urls
     * @apiParam {String[]} [config.headers=[]] Headers
     * @apiParam {String} [config.response_code=] Response code
     * @apiParam {Boolean} [config.insecure_skip_verify=False] Insecure skip verify
     * @apiParam {Object[]} [config.hosts] Hosts
     * @apiParam {String} [config.hosts.ip] Ip
     * @apiParam {String} [config.hosts.outer_ip] Outer ip
     * @apiParam {String} [config.hosts.target_type] Target type
     * @apiParam {Integer} [config.hosts.bk_biz_id] Bk biz id
     * @apiParam {Integer} [config.hosts.bk_inst_id] Bk inst id
     * @apiParam {String} [config.hosts.bk_obj_id] Bk obj id
     * @apiParam {String} [config.hosts.node_path] Node path
     * @apiParam {String} [config.port] Port
     * @apiParam {String} [config.request] Request
     * @apiParam {Integer} [config.max_rtt] Max rtt
     * @apiParam {Integer} [config.total_num] Total num
     * @apiParam {Integer} [config.size] Size
     * @apiParam {Integer} config.period Period
     * @apiParam {String} [config.response_format] Response format
     * @apiParam {String} [config.response] Response
     * @apiParam {Integer} [config.timeout] Timeout
     * @apiParam {String} location Location
     * @apiParam {String[]} node_id_list Node id list
     * @apiParam {String[]} [group_id_list] Group id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 任务名称
     * @apiParam {String="TCP","UDP","HTTP","ICMP"} protocol 协议
     * @apiParam {Integer} [check_interval] 拨测周期(分钟)
     * @apiParam {String="new_draft","running","stoped","starting","stoping","start_failed","stop_failed"} [status] 当前状态
     *
    */
    changeStatus: RestDetailAPI('POST', 'rest/v2/uptime_check/uptime_check_task/{pk}/change_status/'),
    
    /**
     * @apiDescription 克隆任务
     * @api { POST } /rest/v2/uptime_check/uptime_check_task/{pk}/clone/ Clone
     * @apiName Clone
     * @apiGroup uptimeCheckTask
     * @apiParam {Object} config Config
     * @apiParam {String} [config.method] Method
     * @apiParam {String} [config.urls] Urls
     * @apiParam {String[]} [config.headers=[]] Headers
     * @apiParam {String} [config.response_code=] Response code
     * @apiParam {Boolean} [config.insecure_skip_verify=False] Insecure skip verify
     * @apiParam {Object[]} [config.hosts] Hosts
     * @apiParam {String} [config.hosts.ip] Ip
     * @apiParam {String} [config.hosts.outer_ip] Outer ip
     * @apiParam {String} [config.hosts.target_type] Target type
     * @apiParam {Integer} [config.hosts.bk_biz_id] Bk biz id
     * @apiParam {Integer} [config.hosts.bk_inst_id] Bk inst id
     * @apiParam {String} [config.hosts.bk_obj_id] Bk obj id
     * @apiParam {String} [config.hosts.node_path] Node path
     * @apiParam {String} [config.port] Port
     * @apiParam {String} [config.request] Request
     * @apiParam {Integer} [config.max_rtt] Max rtt
     * @apiParam {Integer} [config.total_num] Total num
     * @apiParam {Integer} [config.size] Size
     * @apiParam {Integer} config.period Period
     * @apiParam {String} [config.response_format] Response format
     * @apiParam {String} [config.response] Response
     * @apiParam {Integer} [config.timeout] Timeout
     * @apiParam {String} location Location
     * @apiParam {String[]} node_id_list Node id list
     * @apiParam {String[]} [group_id_list] Group id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 任务名称
     * @apiParam {String="TCP","UDP","HTTP","ICMP"} protocol 协议
     * @apiParam {Integer} [check_interval] 拨测周期(分钟)
     * @apiParam {String="new_draft","running","stoped","starting","stoping","start_failed","stop_failed"} [status] 当前状态
     *
    */
    clone: RestDetailAPI('POST', 'rest/v2/uptime_check/uptime_check_task/{pk}/clone/'),
    
    /**
     * 
     * @api { GET } /rest/v2/uptime_check/uptime_check_task/count/ Count
     * @apiName Count
     * @apiGroup uptimeCheckTask
     * @apiParam {Object} config Config
     * @apiParam {String} [config.method] Method
     * @apiParam {String} [config.urls] Urls
     * @apiParam {String[]} [config.headers=[]] Headers
     * @apiParam {String} [config.response_code=] Response code
     * @apiParam {Boolean} [config.insecure_skip_verify=False] Insecure skip verify
     * @apiParam {Object[]} [config.hosts] Hosts
     * @apiParam {String} [config.hosts.ip] Ip
     * @apiParam {String} [config.hosts.outer_ip] Outer ip
     * @apiParam {String} [config.hosts.target_type] Target type
     * @apiParam {Integer} [config.hosts.bk_biz_id] Bk biz id
     * @apiParam {Integer} [config.hosts.bk_inst_id] Bk inst id
     * @apiParam {String} [config.hosts.bk_obj_id] Bk obj id
     * @apiParam {String} [config.hosts.node_path] Node path
     * @apiParam {String} [config.port] Port
     * @apiParam {String} [config.request] Request
     * @apiParam {Integer} [config.max_rtt] Max rtt
     * @apiParam {Integer} [config.total_num] Total num
     * @apiParam {Integer} [config.size] Size
     * @apiParam {Integer} config.period Period
     * @apiParam {String} [config.response_format] Response format
     * @apiParam {String} [config.response] Response
     * @apiParam {Integer} [config.timeout] Timeout
     * @apiParam {String} location Location
     * @apiParam {String[]} node_id_list Node id list
     * @apiParam {String[]} [group_id_list] Group id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 任务名称
     * @apiParam {String="TCP","UDP","HTTP","ICMP"} protocol 协议
     * @apiParam {Integer} [check_interval] 拨测周期(分钟)
     * @apiParam {String="new_draft","running","stoped","starting","stoping","start_failed","stop_failed"} [status] 当前状态
     *
    */
    count: RestListAPI('GET', 'rest/v2/uptime_check/uptime_check_task/count/'),
    
    /**
     * 
     * @api { POST } /rest/v2/uptime_check/uptime_check_task/ Create
     * @apiName Create
     * @apiGroup uptimeCheckTask
     * @apiParam {Object} config Config
     * @apiParam {String} [config.method] Method
     * @apiParam {String} [config.urls] Urls
     * @apiParam {String[]} [config.headers=[]] Headers
     * @apiParam {String} [config.response_code=] Response code
     * @apiParam {Boolean} [config.insecure_skip_verify=False] Insecure skip verify
     * @apiParam {Object[]} [config.hosts] Hosts
     * @apiParam {String} [config.hosts.ip] Ip
     * @apiParam {String} [config.hosts.outer_ip] Outer ip
     * @apiParam {String} [config.hosts.target_type] Target type
     * @apiParam {Integer} [config.hosts.bk_biz_id] Bk biz id
     * @apiParam {Integer} [config.hosts.bk_inst_id] Bk inst id
     * @apiParam {String} [config.hosts.bk_obj_id] Bk obj id
     * @apiParam {String} [config.hosts.node_path] Node path
     * @apiParam {String} [config.port] Port
     * @apiParam {String} [config.request] Request
     * @apiParam {Integer} [config.max_rtt] Max rtt
     * @apiParam {Integer} [config.total_num] Total num
     * @apiParam {Integer} [config.size] Size
     * @apiParam {Integer} config.period Period
     * @apiParam {String} [config.response_format] Response format
     * @apiParam {String} [config.response] Response
     * @apiParam {Integer} [config.timeout] Timeout
     * @apiParam {String} location Location
     * @apiParam {String[]} node_id_list Node id list
     * @apiParam {String[]} [group_id_list] Group id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 任务名称
     * @apiParam {String="TCP","UDP","HTTP","ICMP"} protocol 协议
     * @apiParam {Integer} [check_interval] 拨测周期(分钟)
     * @apiParam {String="new_draft","running","stoped","starting","stoping","start_failed","stop_failed"} [status] 当前状态
     *
    */
    create: RestListAPI('POST', 'rest/v2/uptime_check/uptime_check_task/'),
    
    /**
     * @apiDescription 正式创建任务
        下发正式配置，采集器托管任务，将采集结果上报至计算平台
     * @api { POST } /rest/v2/uptime_check/uptime_check_task/{pk}/deploy/ Deploy
     * @apiName Deploy
     * @apiGroup uptimeCheckTask
     * @apiParam {Object} config Config
     * @apiParam {String} [config.method] Method
     * @apiParam {String} [config.urls] Urls
     * @apiParam {String[]} [config.headers=[]] Headers
     * @apiParam {String} [config.response_code=] Response code
     * @apiParam {Boolean} [config.insecure_skip_verify=False] Insecure skip verify
     * @apiParam {Object[]} [config.hosts] Hosts
     * @apiParam {String} [config.hosts.ip] Ip
     * @apiParam {String} [config.hosts.outer_ip] Outer ip
     * @apiParam {String} [config.hosts.target_type] Target type
     * @apiParam {Integer} [config.hosts.bk_biz_id] Bk biz id
     * @apiParam {Integer} [config.hosts.bk_inst_id] Bk inst id
     * @apiParam {String} [config.hosts.bk_obj_id] Bk obj id
     * @apiParam {String} [config.hosts.node_path] Node path
     * @apiParam {String} [config.port] Port
     * @apiParam {String} [config.request] Request
     * @apiParam {Integer} [config.max_rtt] Max rtt
     * @apiParam {Integer} [config.total_num] Total num
     * @apiParam {Integer} [config.size] Size
     * @apiParam {Integer} config.period Period
     * @apiParam {String} [config.response_format] Response format
     * @apiParam {String} [config.response] Response
     * @apiParam {Integer} [config.timeout] Timeout
     * @apiParam {String} location Location
     * @apiParam {String[]} node_id_list Node id list
     * @apiParam {String[]} [group_id_list] Group id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 任务名称
     * @apiParam {String="TCP","UDP","HTTP","ICMP"} protocol 协议
     * @apiParam {Integer} [check_interval] 拨测周期(分钟)
     * @apiParam {String="new_draft","running","stoped","starting","stoping","start_failed","stop_failed"} [status] 当前状态
     *
    */
    deploy: RestDetailAPI('POST', 'rest/v2/uptime_check/uptime_check_task/{pk}/deploy/'),
    
    /**
     * 
     * @api { DELETE } /rest/v2/uptime_check/uptime_check_task/{pk}/ Destroy
     * @apiName Destroy
     * @apiGroup uptimeCheckTask
     * @apiParam {Object} config Config
     * @apiParam {String} [config.method] Method
     * @apiParam {String} [config.urls] Urls
     * @apiParam {String[]} [config.headers=[]] Headers
     * @apiParam {String} [config.response_code=] Response code
     * @apiParam {Boolean} [config.insecure_skip_verify=False] Insecure skip verify
     * @apiParam {Object[]} [config.hosts] Hosts
     * @apiParam {String} [config.hosts.ip] Ip
     * @apiParam {String} [config.hosts.outer_ip] Outer ip
     * @apiParam {String} [config.hosts.target_type] Target type
     * @apiParam {Integer} [config.hosts.bk_biz_id] Bk biz id
     * @apiParam {Integer} [config.hosts.bk_inst_id] Bk inst id
     * @apiParam {String} [config.hosts.bk_obj_id] Bk obj id
     * @apiParam {String} [config.hosts.node_path] Node path
     * @apiParam {String} [config.port] Port
     * @apiParam {String} [config.request] Request
     * @apiParam {Integer} [config.max_rtt] Max rtt
     * @apiParam {Integer} [config.total_num] Total num
     * @apiParam {Integer} [config.size] Size
     * @apiParam {Integer} config.period Period
     * @apiParam {String} [config.response_format] Response format
     * @apiParam {String} [config.response] Response
     * @apiParam {Integer} [config.timeout] Timeout
     * @apiParam {String} location Location
     * @apiParam {String[]} node_id_list Node id list
     * @apiParam {String[]} [group_id_list] Group id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 任务名称
     * @apiParam {String="TCP","UDP","HTTP","ICMP"} protocol 协议
     * @apiParam {Integer} [check_interval] 拨测周期(分钟)
     * @apiParam {String="new_draft","running","stoped","starting","stoping","start_failed","stop_failed"} [status] 当前状态
     *
    */
    destroy: RestDetailAPI('DELETE', 'rest/v2/uptime_check/uptime_check_task/{pk}/'),
    
    /**
     * @apiDescription 重写list，传入get_groups时整合拨测任务组卡片页数据，避免数据库重复查询
     * @api { GET } /rest/v2/uptime_check/uptime_check_task/ List
     * @apiName List
     * @apiGroup uptimeCheckTask
     * @apiParam {Object} config Config
     * @apiParam {String} [config.method] Method
     * @apiParam {String} [config.urls] Urls
     * @apiParam {String[]} [config.headers=[]] Headers
     * @apiParam {String} [config.response_code=] Response code
     * @apiParam {Boolean} [config.insecure_skip_verify=False] Insecure skip verify
     * @apiParam {Object[]} [config.hosts] Hosts
     * @apiParam {String} [config.hosts.ip] Ip
     * @apiParam {String} [config.hosts.outer_ip] Outer ip
     * @apiParam {String} [config.hosts.target_type] Target type
     * @apiParam {Integer} [config.hosts.bk_biz_id] Bk biz id
     * @apiParam {Integer} [config.hosts.bk_inst_id] Bk inst id
     * @apiParam {String} [config.hosts.bk_obj_id] Bk obj id
     * @apiParam {String} [config.hosts.node_path] Node path
     * @apiParam {String} [config.port] Port
     * @apiParam {String} [config.request] Request
     * @apiParam {Integer} [config.max_rtt] Max rtt
     * @apiParam {Integer} [config.total_num] Total num
     * @apiParam {Integer} [config.size] Size
     * @apiParam {Integer} config.period Period
     * @apiParam {String} [config.response_format] Response format
     * @apiParam {String} [config.response] Response
     * @apiParam {Integer} [config.timeout] Timeout
     * @apiParam {String} location Location
     * @apiParam {String[]} node_id_list Node id list
     * @apiParam {String[]} [group_id_list] Group id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 任务名称
     * @apiParam {String="TCP","UDP","HTTP","ICMP"} protocol 协议
     * @apiParam {Integer} [check_interval] 拨测周期(分钟)
     * @apiParam {String="new_draft","running","stoped","starting","stoping","start_failed","stop_failed"} [status] 当前状态
     *
    */
    list: RestListAPI('GET', 'rest/v2/uptime_check/uptime_check_task/'),
    
    /**
     * 
     * @api { PATCH } /rest/v2/uptime_check/uptime_check_task/{pk}/ PartialUpdate
     * @apiName PartialUpdate
     * @apiGroup uptimeCheckTask
     * @apiParam {Object} config Config
     * @apiParam {String} [config.method] Method
     * @apiParam {String} [config.urls] Urls
     * @apiParam {String[]} [config.headers=[]] Headers
     * @apiParam {String} [config.response_code=] Response code
     * @apiParam {Boolean} [config.insecure_skip_verify=False] Insecure skip verify
     * @apiParam {Object[]} [config.hosts] Hosts
     * @apiParam {String} [config.hosts.ip] Ip
     * @apiParam {String} [config.hosts.outer_ip] Outer ip
     * @apiParam {String} [config.hosts.target_type] Target type
     * @apiParam {Integer} [config.hosts.bk_biz_id] Bk biz id
     * @apiParam {Integer} [config.hosts.bk_inst_id] Bk inst id
     * @apiParam {String} [config.hosts.bk_obj_id] Bk obj id
     * @apiParam {String} [config.hosts.node_path] Node path
     * @apiParam {String} [config.port] Port
     * @apiParam {String} [config.request] Request
     * @apiParam {Integer} [config.max_rtt] Max rtt
     * @apiParam {Integer} [config.total_num] Total num
     * @apiParam {Integer} [config.size] Size
     * @apiParam {Integer} config.period Period
     * @apiParam {String} [config.response_format] Response format
     * @apiParam {String} [config.response] Response
     * @apiParam {Integer} [config.timeout] Timeout
     * @apiParam {String} location Location
     * @apiParam {String[]} node_id_list Node id list
     * @apiParam {String[]} [group_id_list] Group id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 任务名称
     * @apiParam {String="TCP","UDP","HTTP","ICMP"} protocol 协议
     * @apiParam {Integer} [check_interval] 拨测周期(分钟)
     * @apiParam {String="new_draft","running","stoped","starting","stoping","start_failed","stop_failed"} [status] 当前状态
     *
    */
    partialUpdate: RestDetailAPI('PATCH', 'rest/v2/uptime_check/uptime_check_task/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v2/uptime_check/uptime_check_task/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup uptimeCheckTask
     * @apiParam {Object} config Config
     * @apiParam {String} [config.method] Method
     * @apiParam {String} [config.urls] Urls
     * @apiParam {String[]} [config.headers=[]] Headers
     * @apiParam {String} [config.response_code=] Response code
     * @apiParam {Boolean} [config.insecure_skip_verify=False] Insecure skip verify
     * @apiParam {Object[]} [config.hosts] Hosts
     * @apiParam {String} [config.hosts.ip] Ip
     * @apiParam {String} [config.hosts.outer_ip] Outer ip
     * @apiParam {String} [config.hosts.target_type] Target type
     * @apiParam {Integer} [config.hosts.bk_biz_id] Bk biz id
     * @apiParam {Integer} [config.hosts.bk_inst_id] Bk inst id
     * @apiParam {String} [config.hosts.bk_obj_id] Bk obj id
     * @apiParam {String} [config.hosts.node_path] Node path
     * @apiParam {String} [config.port] Port
     * @apiParam {String} [config.request] Request
     * @apiParam {Integer} [config.max_rtt] Max rtt
     * @apiParam {Integer} [config.total_num] Total num
     * @apiParam {Integer} [config.size] Size
     * @apiParam {Integer} config.period Period
     * @apiParam {String} [config.response_format] Response format
     * @apiParam {String} [config.response] Response
     * @apiParam {Integer} [config.timeout] Timeout
     * @apiParam {String} location Location
     * @apiParam {String[]} node_id_list Node id list
     * @apiParam {String[]} [group_id_list] Group id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 任务名称
     * @apiParam {String="TCP","UDP","HTTP","ICMP"} protocol 协议
     * @apiParam {Integer} [check_interval] 拨测周期(分钟)
     * @apiParam {String="new_draft","running","stoped","starting","stoping","start_failed","stop_failed"} [status] 当前状态
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v2/uptime_check/uptime_check_task/{pk}/'),
    
    /**
     * @apiDescription 创建拨测任务时，查询部署任务是否成功，失败则返回节点管理中部署失败错误日志
        :return:
     * @api { GET } /rest/v2/uptime_check/uptime_check_task/{pk}/running_status/ RunningStatus
     * @apiName RunningStatus
     * @apiGroup uptimeCheckTask
     * @apiParam {Object} config Config
     * @apiParam {String} [config.method] Method
     * @apiParam {String} [config.urls] Urls
     * @apiParam {String[]} [config.headers=[]] Headers
     * @apiParam {String} [config.response_code=] Response code
     * @apiParam {Boolean} [config.insecure_skip_verify=False] Insecure skip verify
     * @apiParam {Object[]} [config.hosts] Hosts
     * @apiParam {String} [config.hosts.ip] Ip
     * @apiParam {String} [config.hosts.outer_ip] Outer ip
     * @apiParam {String} [config.hosts.target_type] Target type
     * @apiParam {Integer} [config.hosts.bk_biz_id] Bk biz id
     * @apiParam {Integer} [config.hosts.bk_inst_id] Bk inst id
     * @apiParam {String} [config.hosts.bk_obj_id] Bk obj id
     * @apiParam {String} [config.hosts.node_path] Node path
     * @apiParam {String} [config.port] Port
     * @apiParam {String} [config.request] Request
     * @apiParam {Integer} [config.max_rtt] Max rtt
     * @apiParam {Integer} [config.total_num] Total num
     * @apiParam {Integer} [config.size] Size
     * @apiParam {Integer} config.period Period
     * @apiParam {String} [config.response_format] Response format
     * @apiParam {String} [config.response] Response
     * @apiParam {Integer} [config.timeout] Timeout
     * @apiParam {String} location Location
     * @apiParam {String[]} node_id_list Node id list
     * @apiParam {String[]} [group_id_list] Group id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 任务名称
     * @apiParam {String="TCP","UDP","HTTP","ICMP"} protocol 协议
     * @apiParam {Integer} [check_interval] 拨测周期(分钟)
     * @apiParam {String="new_draft","running","stoped","starting","stoping","start_failed","stop_failed"} [status] 当前状态
     *
    */
    runningStatus: RestDetailAPI('GET', 'rest/v2/uptime_check/uptime_check_task/{pk}/running_status/'),
    
    /**
     * @apiDescription 测试任务
        下发测试配置，采集器只执行一次数据采集，直接返回采集结果，不经过计算平台
     * @api { POST } /rest/v2/uptime_check/uptime_check_task/test/ Test
     * @apiName Test
     * @apiGroup uptimeCheckTask
     * @apiParam {Object} config Config
     * @apiParam {String} [config.method] Method
     * @apiParam {String} [config.urls] Urls
     * @apiParam {String[]} [config.headers=[]] Headers
     * @apiParam {String} [config.response_code=] Response code
     * @apiParam {Boolean} [config.insecure_skip_verify=False] Insecure skip verify
     * @apiParam {Object[]} [config.hosts] Hosts
     * @apiParam {String} [config.hosts.ip] Ip
     * @apiParam {String} [config.hosts.outer_ip] Outer ip
     * @apiParam {String} [config.hosts.target_type] Target type
     * @apiParam {Integer} [config.hosts.bk_biz_id] Bk biz id
     * @apiParam {Integer} [config.hosts.bk_inst_id] Bk inst id
     * @apiParam {String} [config.hosts.bk_obj_id] Bk obj id
     * @apiParam {String} [config.hosts.node_path] Node path
     * @apiParam {String} [config.port] Port
     * @apiParam {String} [config.request] Request
     * @apiParam {Integer} [config.max_rtt] Max rtt
     * @apiParam {Integer} [config.total_num] Total num
     * @apiParam {Integer} [config.size] Size
     * @apiParam {Integer} config.period Period
     * @apiParam {String} [config.response_format] Response format
     * @apiParam {String} [config.response] Response
     * @apiParam {Integer} [config.timeout] Timeout
     * @apiParam {String} location Location
     * @apiParam {String[]} node_id_list Node id list
     * @apiParam {String[]} [group_id_list] Group id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 任务名称
     * @apiParam {String="TCP","UDP","HTTP","ICMP"} protocol 协议
     * @apiParam {Integer} [check_interval] 拨测周期(分钟)
     * @apiParam {String="new_draft","running","stoped","starting","stoping","start_failed","stop_failed"} [status] 当前状态
     *
    */
    test: RestListAPI('POST', 'rest/v2/uptime_check/uptime_check_task/test/'),
    
    /**
     * 
     * @api { PUT } /rest/v2/uptime_check/uptime_check_task/{pk}/ Update
     * @apiName Update
     * @apiGroup uptimeCheckTask
     * @apiParam {Object} config Config
     * @apiParam {String} [config.method] Method
     * @apiParam {String} [config.urls] Urls
     * @apiParam {String[]} [config.headers=[]] Headers
     * @apiParam {String} [config.response_code=] Response code
     * @apiParam {Boolean} [config.insecure_skip_verify=False] Insecure skip verify
     * @apiParam {Object[]} [config.hosts] Hosts
     * @apiParam {String} [config.hosts.ip] Ip
     * @apiParam {String} [config.hosts.outer_ip] Outer ip
     * @apiParam {String} [config.hosts.target_type] Target type
     * @apiParam {Integer} [config.hosts.bk_biz_id] Bk biz id
     * @apiParam {Integer} [config.hosts.bk_inst_id] Bk inst id
     * @apiParam {String} [config.hosts.bk_obj_id] Bk obj id
     * @apiParam {String} [config.hosts.node_path] Node path
     * @apiParam {String} [config.port] Port
     * @apiParam {String} [config.request] Request
     * @apiParam {Integer} [config.max_rtt] Max rtt
     * @apiParam {Integer} [config.total_num] Total num
     * @apiParam {Integer} [config.size] Size
     * @apiParam {Integer} config.period Period
     * @apiParam {String} [config.response_format] Response format
     * @apiParam {String} [config.response] Response
     * @apiParam {Integer} [config.timeout] Timeout
     * @apiParam {String} location Location
     * @apiParam {String[]} node_id_list Node id list
     * @apiParam {String[]} [group_id_list] Group id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {Integer} bk_biz_id 业务ID
     * @apiParam {String} name 任务名称
     * @apiParam {String="TCP","UDP","HTTP","ICMP"} protocol 协议
     * @apiParam {Integer} [check_interval] 拨测周期(分钟)
     * @apiParam {String="new_draft","running","stoped","starting","stoping","start_failed","stop_failed"} [status] 当前状态
     *
    */
    update: RestDetailAPI('PUT', 'rest/v2/uptime_check/uptime_check_task/{pk}/'),
    
  },

  uptimeCheckGroup: {
    
    /**
     * @apiDescription 拨测任务拖拽进入任务组
     * @api { POST } /rest/v2/uptime_check/uptime_check_group/{pk}/add_task/ AddTask
     * @apiName AddTask
     * @apiGroup uptimeCheckGroup
     * @apiParam {String[]} task_id_list Task id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {String} name 分组名称
     * @apiParam {String} [logo] 图片base64形式
     * @apiParam {Integer} [bk_biz_id] 业务ID
     *
    */
    addTask: RestDetailAPI('POST', 'rest/v2/uptime_check/uptime_check_group/{pk}/add_task/'),
    
    /**
     * 
     * @api { POST } /rest/v2/uptime_check/uptime_check_group/ Create
     * @apiName Create
     * @apiGroup uptimeCheckGroup
     * @apiParam {String[]} task_id_list Task id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {String} name 分组名称
     * @apiParam {String} [logo] 图片base64形式
     * @apiParam {Integer} [bk_biz_id] 业务ID
     *
    */
    create: RestListAPI('POST', 'rest/v2/uptime_check/uptime_check_group/'),
    
    /**
     * 
     * @api { DELETE } /rest/v2/uptime_check/uptime_check_group/{pk}/ Destroy
     * @apiName Destroy
     * @apiGroup uptimeCheckGroup
     * @apiParam {String[]} task_id_list Task id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {String} name 分组名称
     * @apiParam {String} [logo] 图片base64形式
     * @apiParam {Integer} [bk_biz_id] 业务ID
     *
    */
    destroy: RestDetailAPI('DELETE', 'rest/v2/uptime_check/uptime_check_group/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v2/uptime_check/uptime_check_group/ List
     * @apiName List
     * @apiGroup uptimeCheckGroup
     * @apiParam {String[]} task_id_list Task id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {String} name 分组名称
     * @apiParam {String} [logo] 图片base64形式
     * @apiParam {Integer} [bk_biz_id] 业务ID
     *
    */
    list: RestListAPI('GET', 'rest/v2/uptime_check/uptime_check_group/'),
    
    /**
     * 
     * @api { PATCH } /rest/v2/uptime_check/uptime_check_group/{pk}/ PartialUpdate
     * @apiName PartialUpdate
     * @apiGroup uptimeCheckGroup
     * @apiParam {String[]} task_id_list Task id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {String} name 分组名称
     * @apiParam {String} [logo] 图片base64形式
     * @apiParam {Integer} [bk_biz_id] 业务ID
     *
    */
    partialUpdate: RestDetailAPI('PATCH', 'rest/v2/uptime_check/uptime_check_group/{pk}/'),
    
    /**
     * @apiDescription 简化返回数据
     * @api { GET } /rest/v2/uptime_check/uptime_check_group/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup uptimeCheckGroup
     * @apiParam {String[]} task_id_list Task id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {String} name 分组名称
     * @apiParam {String} [logo] 图片base64形式
     * @apiParam {Integer} [bk_biz_id] 业务ID
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v2/uptime_check/uptime_check_group/{pk}/'),
    
    /**
     * 
     * @api { PUT } /rest/v2/uptime_check/uptime_check_group/{pk}/ Update
     * @apiName Update
     * @apiGroup uptimeCheckGroup
     * @apiParam {String[]} task_id_list Task id list
     * @apiParam {String} [create_user] 创建人
     * @apiParam {String} [update_user] 修改人
     * @apiParam {Boolean} [is_deleted] 是否删除
     * @apiParam {String} name 分组名称
     * @apiParam {String} [logo] 图片base64形式
     * @apiParam {Integer} [bk_biz_id] 业务ID
     *
    */
    update: RestDetailAPI('PUT', 'rest/v2/uptime_check/uptime_check_group/{pk}/'),
    
  },

  collectorPlugin: {
    
    /**
     * 
     * @api { GET } /rest/v2/collector_plugin/check_id/ CheckId
     * @apiName CheckId
     * @apiGroup collectorPlugin
     *
    */
    checkId: RestListAPI('GET', 'rest/v2/collector_plugin/check_id/'),
    
    /**
     * 
     * @api { POST } /rest/v2/collector_plugin/ Create
     * @apiName Create
     * @apiGroup collectorPlugin
     *
    */
    create: RestListAPI('POST', 'rest/v2/collector_plugin/'),
    
    /**
     * 
     * @api { POST } /rest/v2/collector_plugin/delete/ Delete
     * @apiName Delete
     * @apiGroup collectorPlugin
     *
    */
    delete: RestListAPI('POST', 'rest/v2/collector_plugin/delete/'),
    
    /**
     * 
     * @api { DELETE } /rest/v2/collector_plugin/{pk}/ Destroy
     * @apiName Destroy
     * @apiGroup collectorPlugin
     *
    */
    destroy: RestDetailAPI('DELETE', 'rest/v2/collector_plugin/{pk}/'),
    
    /**
     * @apiDescription 插件编辑接口，两种情况：
        1. 普通编辑，file_data 参数为空
        2. 导入覆盖后编辑 file_data 参数不为空
     * @api { POST } /rest/v2/collector_plugin/{pk}/edit/ Edit
     * @apiName Edit
     * @apiGroup collectorPlugin
     *
    */
    edit: RestDetailAPI('POST', 'rest/v2/collector_plugin/{pk}/edit/'),
    
    /**
     * 
     * @api { GET } /rest/v2/collector_plugin/{pk}/export_plugin/ ExportPlugin
     * @apiName ExportPlugin
     * @apiGroup collectorPlugin
     *
    */
    exportPlugin: RestDetailAPI('GET', 'rest/v2/collector_plugin/{pk}/export_plugin/'),
    
    /**
     * 
     * @api { GET } /rest/v2/collector_plugin/{pk}/fetch_debug_log/ FetchDebugLog
     * @apiName FetchDebugLog
     * @apiGroup collectorPlugin
     *
    */
    fetchDebugLog: RestDetailAPI('GET', 'rest/v2/collector_plugin/{pk}/fetch_debug_log/'),
    
    /**
     * 
     * @api { POST } /rest/v2/collector_plugin/import_plugin/ ImportPlugin
     * @apiName ImportPlugin
     * @apiGroup collectorPlugin
     *
    */
    importPlugin: RestListAPI('POST', 'rest/v2/collector_plugin/import_plugin/'),
    
    /**
     * 
     * @api { GET } /rest/v2/collector_plugin/ List
     * @apiName List
     * @apiGroup collectorPlugin
     *
    */
    list: RestListAPI('GET', 'rest/v2/collector_plugin/'),
    
    /**
     * 
     * @api { GET } /rest/v2/collector_plugin/operator_system/ OperatorSystem
     * @apiName OperatorSystem
     * @apiGroup collectorPlugin
     *
    */
    operatorSystem: RestListAPI('GET', 'rest/v2/collector_plugin/operator_system/'),
    
    /**
     * 
     * @api { PATCH } /rest/v2/collector_plugin/{pk}/ PartialUpdate
     * @apiName PartialUpdate
     * @apiGroup collectorPlugin
     *
    */
    partialUpdate: RestDetailAPI('PATCH', 'rest/v2/collector_plugin/{pk}/'),
    
    /**
     * 
     * @api { POST } /rest/v2/collector_plugin/{pk}/release/ Release
     * @apiName Release
     * @apiGroup collectorPlugin
     *
    */
    release: RestDetailAPI('POST', 'rest/v2/collector_plugin/{pk}/release/'),
    
    /**
     * 
     * @api { POST } /rest/v2/collector_plugin/replace_plugin/ ReplacePlugin
     * @apiName ReplacePlugin
     * @apiGroup collectorPlugin
     *
    */
    replacePlugin: RestListAPI('POST', 'rest/v2/collector_plugin/replace_plugin/'),
    
    /**
     * 
     * @api { GET } /rest/v2/collector_plugin/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup collectorPlugin
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v2/collector_plugin/{pk}/'),
    
    /**
     * 
     * @api { POST } /rest/v2/collector_plugin/{pk}/start_debug/ StartDebug
     * @apiName StartDebug
     * @apiGroup collectorPlugin
     *
    */
    startDebug: RestDetailAPI('POST', 'rest/v2/collector_plugin/{pk}/start_debug/'),
    
    /**
     * 
     * @api { POST } /rest/v2/collector_plugin/{pk}/stop_debug/ StopDebug
     * @apiName StopDebug
     * @apiGroup collectorPlugin
     *
    */
    stopDebug: RestDetailAPI('POST', 'rest/v2/collector_plugin/{pk}/stop_debug/'),
    
    /**
     * 
     * @api { GET } /rest/v2/collector_plugin/tag_options/ TagOptions
     * @apiName TagOptions
     * @apiGroup collectorPlugin
     *
    */
    tagOptions: RestListAPI('GET', 'rest/v2/collector_plugin/tag_options/'),
    
    /**
     * 
     * @api { PUT } /rest/v2/collector_plugin/{pk}/ Update
     * @apiName Update
     * @apiGroup collectorPlugin
     *
    */
    update: RestDetailAPI('PUT', 'rest/v2/collector_plugin/{pk}/'),
    
    /**
     * 
     * @api { POST } /rest/v2/collector_plugin/upload_file/ UploadFile
     * @apiName UploadFile
     * @apiGroup collectorPlugin
     *
    */
    uploadFile: RestListAPI('POST', 'rest/v2/collector_plugin/upload_file/'),
    
  },

  queryHistory: {
    
    /**
     * 
     * @api { POST } /rest/v2/query_history/ Create
     * @apiName Create
     * @apiGroup queryHistory
     * @apiParam {String} name 名称
     * @apiParam {String} config Config
     * @apiParam {Integer} bk_biz_id 业务ID
     *
    */
    create: RestListAPI('POST', 'rest/v2/query_history/'),
    
    /**
     * 
     * @api { DELETE } /rest/v2/query_history/{pk}/ Destroy
     * @apiName Destroy
     * @apiGroup queryHistory
     * @apiParam {String} name 名称
     * @apiParam {String} config Config
     * @apiParam {Integer} bk_biz_id 业务ID
     *
    */
    destroy: RestDetailAPI('DELETE', 'rest/v2/query_history/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v2/query_history/ List
     * @apiName List
     * @apiGroup queryHistory
     * @apiParam {String} name 名称
     * @apiParam {String} config Config
     * @apiParam {Integer} bk_biz_id 业务ID
     *
    */
    list: RestListAPI('GET', 'rest/v2/query_history/'),
    
    /**
     * 
     * @api { PATCH } /rest/v2/query_history/{pk}/ PartialUpdate
     * @apiName PartialUpdate
     * @apiGroup queryHistory
     * @apiParam {String} name 名称
     * @apiParam {String} config Config
     * @apiParam {Integer} bk_biz_id 业务ID
     *
    */
    partialUpdate: RestDetailAPI('PATCH', 'rest/v2/query_history/{pk}/'),
    
    /**
     * 
     * @api { GET } /rest/v2/query_history/{pk}/ Retrieve
     * @apiName Retrieve
     * @apiGroup queryHistory
     * @apiParam {String} name 名称
     * @apiParam {String} config Config
     * @apiParam {Integer} bk_biz_id 业务ID
     *
    */
    retrieve: RestDetailAPI('GET', 'rest/v2/query_history/{pk}/'),
    
    /**
     * 
     * @api { PUT } /rest/v2/query_history/{pk}/ Update
     * @apiName Update
     * @apiGroup queryHistory
     * @apiParam {String} name 名称
     * @apiParam {String} config Config
     * @apiParam {Integer} bk_biz_id 业务ID
     *
    */
    update: RestDetailAPI('PUT', 'rest/v2/query_history/{pk}/'),
    
  },

}

export {
  Model,
  Resource
}


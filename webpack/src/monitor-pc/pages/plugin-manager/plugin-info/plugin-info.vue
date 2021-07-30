<template>
  <div class="plugin-detail-wrapper" v-bkloading="{ isLoading: isLoading }">
    <div class="tab">
      <div :class="{ 'btn': true, 'active': tabActive === 'detail' }" @click="handleTabChange('detail')"> {{ $t('插件详情') }} </div>
      <div v-if="pluginInfo.status === 'normal'" :class="{ 'btn': true, 'active': tabActive === 'metric' }" @click="handleTabChange('metric')"> {{ $t('指标维度') }} </div>
    </div>
    <div class="content-wrapper">
      <div class="operator">
        <div v-show="tabActive === 'detail'">
          <span class="text"> {{ $t('如需变更插件请点击') }} </span>
          <span
            v-if="canEdit"
            class="btn text"
            v-authority="{ active: !authority.MANAGE_AUTH }"
            @click="authority.MANAGE_AUTH ? handleEdit() : handleShowAuthorityDetail()">
            {{ $t('编辑插件') }}
          </span>
          <span class="btn text" @click="handleLook"> {{ $t('查看变更记录') }} </span>
        </div>
        <div v-show="tabActive === 'metric'">
          <span class="text"> {{ $t('如需变更编辑指标&维度请点击') }} </span>
          <span
            class="btn text"
            v-authority="{ active: !authority.MANAGE_AUTH }"
            @click="authority.MANAGE_AUTH ? handleToMertic() : handleShowAuthorityDetail()">
            {{ $t('设置指标&维度') }}
          </span>
        </div>
      </div>
      <div v-show="tabActive === 'metric'">
        <div class="metric-group" :class="{ 'active-group': show }" v-for="group in pluginInfo.metric_json" :key="group.table_name">
          <div class="group-header">
            <div class="left-box" @click="show = !show">
              <i class="bk-icon group-icon" :class="show ? 'icon-right-shape' : 'icon-down-shape'"></i>
              <div class="group-name">{{ group.table_name }}({{ group.table_desc }})</div>
              <div class="group-num">{{ $t('共') }} <span class="num-blod">{{ metricNum(group.fields) }}</span> {{ $t('个指标，') }}<span class="num-blod">{{ dimensionNum(group.fields) }}</span> {{ $t('个维度') }}</div>
            </div>
          </div>
          <div class="table-box">
            <div class="left-table">
              <bk-table :data="group.fields" :outer-border="false">
                <bk-table-column :label="$t('指标/维度')" width="120">
                  <template slot-scope="scope">
                    <div v-if="scope.row.monitor_type === 'metric'">{{ $t('指标') }}</div>
                    <div v-else>{{ $t('维度') }}</div>
                  </template>
                </bk-table-column>
                <bk-table-column :label="$t('英文名')" min-width="100" prop="name">
                </bk-table-column>
                <bk-table-column :label="$t('别名')" min-width="100">
                  <template slot-scope="scope">
                    {{ scope.row.description || '--' }}
                  </template>
                </bk-table-column>
                <bk-table-column :label="$t('类型')" min-width="60" prop="type">
                </bk-table-column>
                <bk-table-column :label="$t('单位')" min-width="60">
                  <template slot-scope="scope">
                    {{ scope.row.unit || '--' }}
                  </template>
                </bk-table-column>
                <bk-table-column :label="$t('启/停')" width="100">
                  <template slot-scope="scope">
                    <div class="is-active">
                      <div class="active-status" :class="scope.row.is_active ? 'green' : 'red'"></div>
                      <div>{{ scope.row.is_active ? $t('启用') : $t('停用') }}</div>
                    </div>
                  </template>
                </bk-table-column>
              </bk-table>
            </div>
          </div>
        </div>
      </div>
      <div v-show="tabActive === 'detail'" class="plugin-info" ref="pluginInfo">
        <div class="info-item">
          <div class="item-label"> {{ $t('所属业务') }} </div>
          <div class="item-container">
            {{businessName}}
          </div>
          <div class="logo">
            <img class="logo-img" v-if="pluginInfo.logo" :src="`data:image/png;base64,${pluginInfo.logo}`">
            <div class="logo-text" v-else>
              <span class="text-content">{{pluginInfo.plugin_id.slice(0,1).toUpperCase()}}</span>
            </div>
          </div>
        </div>
        <div class="info-item">
          <div class="item-label"> {{ $t('插件ID') }} </div>
          <div class="item-container">
            {{pluginInfo.plugin_id}}
            <span class="public-plugin" v-if="!pluginInfo.bk_biz_id"> {{ $t('( 公共插件 )') }}</span>
          </div>
        </div>
        <div class="info-item">
          <div class="item-label"> {{ $t('插件别名') }} </div>
          <div class="item-container">
            {{pluginInfo.plugin_display_name}}
          </div>
        </div>
        <div class="info-item">
          <div class="item-label"> {{ $t('插件类型') }} </div>
          <div class="item-container">{{pluginType[pluginInfo.plugin_type]}}</div>
        </div>
        <!-- <div class="info-item" v-if="pluginInfo.plugin_type === 'DataDog'">
                    <div class="item-label"> {{ $t('支持系统') }} </div>
                    <div class="item-container">
                        {{pluginInfo.os_type_list.join('、')}}
                    </div>
                </div> -->
        <div class="info-item align-top" v-if="['Exporter', 'DataDog'].includes(pluginInfo.plugin_type)">
          <div class="item-label"> {{ $t('上传内容') }} </div>
          <div class="item-container">
            <div class="exporter">
              <template v-for="(collector, key) in pluginInfo.collector_json">
                <div v-if="collector && collector.file_name" class="file-wrapper" :key="key">
                  <div class="icon-wrapper">
                    <span :class="['item-icon', 'icon-monitor', `icon-${key}`]"></span>
                  </div>
                  <div class="file-name">{{collector.file_name}}</div>
                </div>
              </template>
            </div>
          </div>
        </div>
        <div class="info-item align-top" v-if="['Script', 'JMX', 'DataDog'].includes(pluginInfo.plugin_type)">
          <div class="item-label label-upload">{{$t('采集配置')}}</div>
          <div :class="{ 'item-container': true, 'editor-wrapper': ['Script'].includes(pluginInfo.plugin_type) } " ref="collectorConfig">
            <template v-if="['Script'].includes(pluginInfo.plugin_type)">
              <ul class="system-tabs" v-if="pluginInfo.plugin_type === 'Script'">
                <template v-for="(collector, key) in pluginInfo.systemList">
                  <li :class="['system-tab', { 'active': collectorConf.active === collector }]"
                      :key="key"
                      v-if="collector"
                      @click="viewCollectorConf(collector)">
                    <span>{{collector}}</span>
                  </li>
                </template>
              </ul>
              <div class="script-type"><span>{{collectorConf.type}}</span></div>
              <monaco-editor full-screen :options="editorOptions" v-model="collectorConf.content" language="shell"></monaco-editor>
            </template>
            <div class="jmx" v-if="['JMX', 'DataDog'].includes(pluginInfo.plugin_type)">
              <pre class="jmx-code">{{pluginInfo.collector_json.config_yaml}}</pre>
            </div>
          </div>
        </div>
        <template v-if="pluginInfo.plugin_type === 'Exporter'">
          <div class="info-item">
            <div class="item-label"> {{ $t('绑定端口') }} </div>
            <div class="item-container">
              <span>{{pluginInfo.port}}</span>
              <span class="item-exporter-desc"> {{ $t('变量为“${host}”') }} </span>
            </div>
          </div>
          <div class="info-item">
            <div class="item-label"> {{ $t('绑定主机') }} </div>
            <div class="item-container">
              <span>{{pluginInfo.host}}</span>
              <span class="item-exporter-desc"> {{ $t('变量为“${host}”') }} </span>
            </div>
          </div>
        </template>
        <div :class="{ 'info-item': true, 'multiple-lin': isMultipleLin }">
          <div :class="{ 'item-label': true, 'label-param': pluginInfo.config_json.length ,'multiple-lin': isMultipleLin }"> {{ $t('定义参数') }} </div>
          <div class="item-container" v-if="isShowParam" ref="pluginParams">
            <template v-for="(param, index) in pluginInfo.config_json">
              <span v-if="!param.hasOwnProperty('visible')"
                    :class="{ 'item-param': true, 'multiple-lin': param.multipleLin }"
                    :key="index"
                    @click="viewParam(param)">
                {{param.description || param.name}}
              </span>
            </template>
          </div>
          <div class="item-container no-param" v-else>
            <span class="param-text"> {{ $t('暂未定义脚本参数') }} </span>
          </div>
        </div>
        <div class="info-item">
          <div class="item-label"> {{ $t('远程采集') }} </div>
          <div class="item-container">
            <span v-if="pluginInfo.is_support_remote"> {{ $t('支持') }} </span>
            <span v-else> {{ $t('不支持') }} </span>
          </div>
        </div>
        <div class="info-item">
          <div class="item-label"> {{ $t('分类') }} </div>
          <div class="item-container">{{pluginInfo.label}}</div>
        </div>
        <div class="info-item desc-editor">
          <div class="item-label"> {{ $t('描述') }} </div>
          <div class="item-container">
            <div class="md-editor">
              <viewer :value="pluginInfo.description_md" height="515px"></viewer>
            </div>
          </div>
        </div>
      </div>
    </div>
    <view-param :conf="paramConf" :title="title"></view-param>
  </div>
</template>
<script>
import MonacoEditor from '../../../components/editors/monaco-editor'
import ViewParam from './view-param'
import Viewer from '../../../components/markdown-editor/markdown-viewer'
import { mapActions, mapGetters } from 'vuex'
import { retrieveCollectorPlugin } from '../../../../monitor-api/modules/model'
import { addListener, removeListener } from 'resize-detector'
import authorityMixinCreate from '../../../mixins/authorityMixin'
import * as pluginManagerAuth from '../authority-map'
export default {
  name: 'PluginDetail',
  components: {
    MonacoEditor,
    ViewParam,
    Viewer
  },
  mixins: [authorityMixinCreate(pluginManagerAuth)],
  props: {
    pluginId: String
  },
  data() {
    return {
      show: false,
      isLoading: true,
      title: this.$t('参数详情'),
      tabActive: 'detail',
      paramConf: {
        isShow: false,
        list: []
      },
      editorOptions: {
        readOnly: true,
        width: '100%'
      },
      pluginInfo: {
        bk_biz_id: '',
        plugin_id: '',
        plugin_display_name: '',
        plugin_type: '',
        collector_json: {},
        systemList: [],
        config_json: [],
        metric_json: [],
        tag: '',
        description_md: '',
        config_version: 1,
        info_version: 1,
        host: '',
        label: '',
        port: '',
        logo: '',
        is_support_remote: false
      },
      collectorConf: {
        active: '',
        type: '',
        content: ''
      },
      configLabels: {
        mode: this.$t('参数类型1'),
        name: this.$t('参数名称1'),
        default: this.$t('默认值'),
        description: this.$t('参数说明1')
      },
      types: {
        text: this.$t('文本'),
        password: this.$t('密码'),
        file: this.$t('文件'),
        switch: this.$t('开关')
      },
      pluginType: {
        Script: 'Script',
        JMX: 'JMX',
        Exporter: 'Exporter',
        DataDog: 'DataDog',
        'Built-In': 'BK-Monitor',
        Pushgateway: 'BK-Pull',
        SNMP: 'SNMP'
      },
      updateInfo: [],
      isMultipleLin: false,
      canEdit: true,
      calculationSize: () => {}
    }
  },
  computed: {
    business() {
      const obj = {}
      const list = this.$store.getters.bizList.concat([{ id: 0, text: this.$t('全业务') }])
      list.forEach((item) => {
        obj[item.id] = item.text
      })
      return obj
    },
    businessName() {
      return this.business[this.pluginInfo.bk_biz_id]
    },
    isShowParam() {
      return !!this.pluginInfo.config_json.find(item => !Object.prototype.hasOwnProperty.call(item, 'visible'))
    },
    ...mapGetters('plugin-manager', ['osList', 'labels'])
  },
  watch: {
    isShowParam(val) {
      if (val) {
        this.calculationParamsHeight()
      }
    }
  },
  async created() {
    if (!this.$route.meta.title) {
      this.$store.commit(
        'app/SET_NAV_TITLE',
        `${this.$t('route-' + '插件详情').replace('route-', '')} - ${this.$route.params.pluginId}`
      )
    }
    await Promise.all([this.getOsList(), this.getLabels()]).catch(() => {
      // console.error(error)
    })
    this.requestPluginDetail(this.$route.params.pluginId)
  },
  mounted() {
    this.calculationSize = () => {
      this.calculationEditWidth()
      this.calculationParamsHeight()
    }
    addListener(this.$refs.pluginInfo, this.calculationSize)
  },
  beforeDestroy() {
    removeListener(this.$refs.pluginInfo, this.calculationSize)
  },
  methods: {
    ...mapActions('plugin-manager', ['getOsList', 'getLabels']),
    handleTabChange(name) {
      this.tabActive = name
    },
    handleEdit() {
      this.$router.push({
        name: 'plugin-edit',
        params: {
          pluginId: this.pluginInfo.plugin_id
        }
      })
    },
    handleToMertic() {
      this.$router.push({
        name: 'plugin-setmetric',
        params: {
          pluginId: this.$route.params.pluginId
        }
      })
    },
    handleLook() {
      this.title = this.$t('变更记录')
      this.paramConf.list = this.updateInfo
      this.paramConf.isShow = true
    },
    calculationEditWidth() {
      this.editorOptions.width = this.$refs.collectorConfig && this.$refs.collectorConfig.clientWidth
    },
    /**
             * 计算参数列表高度，判断元素是否换行
             * 24为一行时的初始高度， 34为多行切回到1行时的高度
             */
    calculationParamsHeight() {
      const timer = setTimeout(() => {
        if (this.$refs.pluginParams) {
          const height = this.$refs.pluginParams.clientHeight
          this.isMultipleLin = height > 24 || (height === 34)
          this.pluginInfo.config_json.forEach((item) => {
            this.$set(item, 'multipleLin', !Object.prototype.hasOwnProperty.call(item, 'visible') && this.isMultipleLin)
          })
        }
        clearTimeout(timer)
      }, 16)
    },
    /**
             * @desc 请求插件详情
             * @param {String} id - 插件 ID
             */
    requestPluginDetail(id) {
      retrieveCollectorPlugin(id).then((data) => {
        this.handleData(data)
      })
        .finally(() => {
          this.isLoading = false
        })
    },
    /**
             * @desc 查看采集配置
             * @param {String} key
             */
    viewCollectorConf(key) {
      if (this.pluginInfo.plugin_type === 'DataDog') {
        this.collectorConf.content = this.pluginInfo.collector_json.config_yaml
        return
      }
      const collectorJson = this.pluginInfo.collector_json[key]
      if (collectorJson) {
        const { collectorConf } = this
        collectorConf.active = key
        collectorConf.type = collectorJson.ext
        const res = window.escape(window.atob(collectorJson.script_content_base64 || ''))
        collectorConf.content = window.decodeURIComponent(res)
      }
    },
    /**
             * @desc 查看参数
             * @param {Object} param
             */
    viewParam(param) {
      this.paramConf.list = []
      this.title = this.$t('定义参数')
      Object.keys(this.configLabels).forEach((key) => {
        this.paramConf.list.push({
          label: this.configLabels[key],
          value: key === 'default' ? `${this.types[param.type]}=${param[key]}` : param[key]
        })
      })
      this.paramConf.isShow = true
    },
    parseUrlStr(url) {
      const obj = {}
      const pattern = /^https?:\/\/(([a-zA-Z0-9_-])+(\.)?)*(:\d+)?(\/((\.)?(\?)?=?&?[a-zA-Z0-9_-](\?)?)*)*$/i
      if (url && pattern.test(url)) {
        const url = /^(?:([A-Za-z]+):)?(\/{0,3})([0-9.\-A-Za-z]+)(?::(\d+))?(?:\/([^?#]*))?(?:\?([^#]*))?(?:#(.*))?$/
        const fields = ['url', 'scheme', 'slash', 'host', 'port', 'path', 'query', 'hash']
        const result = url.exec(url)
        fields.forEach((item, index) => {
          obj[item] = result[index]
        })
      }
      return obj
    },
    handleData(data) {
      const pluginInfo = data
      this.pluginInfo = data
      const collectorJson = pluginInfo.collector_json
      const configJson = pluginInfo.config_json
      const type = data.plugin_type
      this.canEdit = data.edit_allowed
      if ((type === 'Script' || type === 'DataDog') && collectorJson) {
        // 默认选中非空的系统展示其脚本内容
        this.pluginInfo.systemList = Object.keys(collectorJson)
          .filter(item => this.osList.find(sys => item === sys.os_type))
        this.pluginInfo.systemList.some(item => collectorJson[item] && this.viewCollectorConf(item))
      } else if (type === 'Exporter') {
        const hostParam = configJson.find(item => item.name === 'host') || {}
        const portParam = configJson.find(item => item.name === 'port') || {}
        pluginInfo.host = hostParam.default
        pluginInfo.port = portParam.default
      }
      this.updateInfo = [
        { label: this.$t('创建人'), value: data.create_user || '--' },
        { label: this.$t('创建时间'), value: data.create_time || '--' },
        { label: this.$t('最后修改者'), value: data.update_user || '--' },
        { label: this.$t('修改时间'), value: data.update_time || '--' }
      ]
      this.labels.forEach((item) => {
        const obj = item.children.find(v => v.id === data.label)
        if (obj) {
          this.pluginInfo.label = `${item.name}-${obj.name}`
        }
      })
    },
    metricNum(data) {
      return data.filter(item => item.monitor_type === 'metric').length
    },
    dimensionNum(data) {
      return data.filter(item => item.monitor_type === 'dimension').length
    }
  }
}
</script>
<style lang="scss" scoped>
.plugin-detail-wrapper {
  margin: -20px -24px 0 -24px;
  height: calc(100vh - 52px);
  overflow: hidden;
}
.tab {
  height: 32px;
  padding-left: 24px;
  padding-top: 3px;
  font-size: 0;
  background: #fff;
  border-bottom: 1px solid #dcdee5;
  box-shadow: 0 3px 4px 0 rgba(64, 112, 203, .06);
  .btn {
    display: inline-block;
    height: 100%;
    font-size: 14px;
    margin-right: 30px;
    cursor: pointer;
  }
  .active {
    color: #3a84ff;
    border-bottom: 2px solid #3a84ff;
  }
}
.operator {
  margin-bottom: 15px;
  font-size: 0;
  .text {
    margin-right: 16px;
    color: #63656e;
    font-size: 12px;
  }
  .btn {
    color: #3a84ff;
    cursor: pointer;
  }
}
.active-group {
  height: 64px;
  overflow: hidden;
}
.content-wrapper {
  height: calc(100% - 32px);
  padding: 17px 20px 20px 26px;
  overflow: auto;
}
.metric-group {
  background: #fff;
  margin-bottom: 8px;
  color: #63656e;
  padding: 0 23px 30px 22px;
  box-shadow: 0 1px 2px 0 rgba(0,0,0,.10);
  transition: height .5s;
  .num-blod {
    font-weight: bold;
  }
  .group-header {
    display: flex;
    align-items: center;
    height: 64px;
    .left-box {
      flex-grow: 1;
      display: flex;
      align-items: center;
      height: 64px;
      cursor: pointer;
      .group-icon {
        font-size: 15px;
        margin-right: 6px;
      }
      .group-name {
        font-size: 14px;
        font-weight: bold;
        margin-right: 40px;
      }
      .group-num {
        color: #979ba5;
        cursor: default;
      }
    }
  }
  .table-box {
    display: flex;
    padding: 0 7px 0 8px;
    overflow-y: scroll;
    max-height: 427px;
    .left-table {
      width: 100%;
      .is-active {
        display: flex;
        align-items: center;
        .active-status {
          height: 8px;
          width: 8px;
          border: 1px solid;
          border-radius: 50%;
          margin-right: 4px;
        }
        .green {
          background: #70eab8;
          border-color: #10c178;
        }
        .red {
          background: #fd9c9c;
          border-color: #ea3636;
        }
      }
    }
  }
}
.plugin-info {
  background: #fff;
  padding-top: 37px;
  padding-right: 40px;
  .info-item {
    display: flex;
    position: relative;
    flex-direction: row;
    margin-bottom: 20px;
    align-items: center;
    .item-label {
      flex: 0 0 116px;
      margin-right: 24px;
      color: #979ba5;
      text-align: right;
      font-size: 12px;
      &.label-param {
        margin-top: 2px;
        align-self: flex-start;
      }
    }
    &.align-top {
      align-items: flex-start;
      .item-label {
        margin-top: 7px;
      }
    }
    &.desc-editor {
      align-items: start;
      padding-bottom: 40px;
    }
    &:last-child {
      margin-bottom: 0;
    }
    .item-container {
      position: relative;
      color: #63656e;
      flex: 1;
      overflow: hidden;
      font-size: 12px;
      &.editor-wrapper {
        height: 395px;
      }
      .public-plugin {
        color: #c4c6cc;
      }
      .item-exporter-desc {
        height: 19px;
        line-height: 19px;
        margin-left: 10px;
        font-size: 14px;
        color: #c4c6cc;
      }
      .exporter {
        display: flex;
        flex-wrap: wrap;
        .file-wrapper {
          display: flex;
          align-items: center;
          width: 438px;
          height: 32px;
          background: #fafbfd;
          border-radius: 2px;
          border: 1px solid #dcdee5;
          .icon-wrapper {
            padding: 0 10px;
            height: 100%;
            .item-icon {
              position: relative;
              display: inline-block;
              height: 100%;
              width: 100%;
              text-align: center;
              line-height: 32px;
              font-size: 15px;
              overflow: hidden;
            }
          }
          .file-name {
            flex: 1;
            max-width: 394px;
            padding-right: 15px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          &:not(:last-child) {
            margin-right: 10px;
            margin-bottom: 10px;
          }
        }
      }
      .system-tabs {
        margin: 0;
        padding: 0;
        display: flex;
        align-items: center;
        background: #fafbfd;
        border: 1px solid #dcdee5;
        border-bottom: 0;
        .system-tab {
          flex: 0 0 140px;
          border-right: 1px solid #dcdee5;
          text-align: center;
          line-height: 42px;
          cursor: pointer;
          &.active {
            position: relative;
            background: #fff;
            &::after {
              position: absolute;
              left: 0;
              content: "";
              background: #3a84ff;
              width: 100%;
              height: 2px;
            }
          }
        }
      }
      .script-type {
        height: 32px;
        line-height: 32px;
        background: #202024;
        span {
          display: inline-block;
          background-color: #313238;
          padding: 0 20px;
        }
      }
      .jmx {
        max-height: 345px;
        overflow-y: scroll;
        padding: 16px 20px;
        background: #313238;
        border-radius: 2px;
        border: 1px solid  #dcdee5;
        .jmx-code {
          font-size: 12px;
          color: #c4c6cc;
          line-height: 17px;
          padding: 0;
          margin: 0;
          border: 0;
        }
      }
      .item-param {
        display: inline-block;
        cursor: pointer;
        height: 24px;
        line-height: 24px;
        text-align: center;
        background-color: #f0f1f5;
        padding: 0 10px;
        margin-right: 10px;
        border-radius: 2px;
        font-size: 12px;
        &:hover {
          background: #e1ecff;
          color: #3a84ff;
        }
      }
      .table-container {
        .start {
          color: #2dcb56;
        }
        .stop {
          color: #c4c6cc;
        }
      }
      .md-editor {
        max-height: 537px;
        overflow-y: scroll;
        border-radius: 2px;
        border: 1px solid #dcdee5;
        padding: 15px 40px 17px 20px;
      }
      &.no-param {
        display: inline-flex;
        align-items: center;
        .param-icon {
          width: 16px;
          height: 16px;
          margin-right: 7px;
          color: #ffa327;
        }
        .param-text {
          height: 19px;
          line-height: 20px;
        }
      }
      .remote-checkbox {
        margin-bottom: 0px;
      }
    }
    .logo {
      position: absolute;
      top: -5px;
      right: 0;
      width: 84px;
      height: 84px;
      border: 1px solid #dcdee5;
      padding: 3px;
      background-color: #fafbfd;
      .logo-img {
        width: 100%;
        height: 100%;
      }
      .logo-text {
        width: 100%;
        height: 100%;
        background: #9cabc4;
        display: inline-flex;
        justify-content: center;
        align-items: center;
        .text-content {
          width: 27px;
          height: 50px;
          line-height: 50px;
          text-align: center;
          font-size: 36px;
          font-weight: 600;
          color: #fff;
        }
      }
    }
  }
  .multiple-lin {
    margin-bottom: 10px;
  }
}

</style>

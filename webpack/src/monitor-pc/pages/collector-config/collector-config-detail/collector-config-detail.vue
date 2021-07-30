<template>
  <bk-sideslider class="collector-config-detail" :is-show="sideShow" @update:isShow="handleHidden" :width="900" :quick-close="true">
    <div slot="header" class="detail-header">
      <span v-if="!loading" class="detail-header-title">{{ `${$t('采集详情')} - #${basicInfo.id} ${name}` }}</span>
      <span v-else>{{ $t('加载中...') }}</span>
      <bk-button
        v-authority="{ active: !authority.MANAGE_AUTH && sideData.status !== 'STOPPED' }"
        v-if="!loading && basicInfo.collect_type !== 'Log'"
        theme="primary"
        :outline="true"
        style="margin-right: 30px"
        @click="authority.MANAGE_AUTH || sideData.status === 'STOPPED' ? sideData.status !== 'STOPPED' && handleToEdit() : handleShowAuthorityDetail()"
        :disabled="sideData.status === 'STOPPED'">
        {{ $t('编辑') }}
      </bk-button>
    </div>
    <div class="detail-content" slot="content" v-bkloading="{ isLoading: loading }">
      <div class="detail-content-tab clearfix">
        <span class="tab-item" @click="active = 0" :class="{ 'tab-active': active === 0 }"> {{ $t('基本信息') }} </span>
        <span class="tab-item" @click="active = 1" :class="{ 'tab-active': active === 1 }"> {{ $t('采集目标') }} </span>
      </div>
      <div class="detail-content-wrap">
        <div class="basic-info" v-show="active === 0">
          <ul class="basic-info-detail" v-if="basicInfo">
            <li class="detail-item" v-for="(item,key) in basicInfoMap" :key="key">
              <div class="detail-item-label" :class="{ 'detail-item-name': key === 'name' }">{{item}}：</div>
              <span
                v-if="key === 'name'"
                v-authority="{ active: !authority.MANAGE_AUTH }"
                class="detail-item-val"
                style="line-height: 32px;"
                @click="authority.MANAGE_AUTH ? handleEditLabel(key) : handleShowAuthorityDetail()">
                <span v-if="!input.show" class="name-wrapper"><span class="config-name" v-bk-tooltips.top="basicInfo[key]">{{basicInfo[key]}}</span><i class="icon-monitor icon-bianji col-name-icon" v-if="!input.show"></i></span>
                <bk-input v-if="input.show"
                          :ref="'input' + key"
                          style="width: 150px"
                          :maxlength="50"
                          v-model="input.copyName"
                          @keydown="handleLabelKey"
                          v-bk-clickoutside="handleTagClickout">
                </bk-input>
              </span>
              <span v-if="key === 'id'" class="detail-item-val">{{basicInfo[key]}}</span>
              <span v-if="key === 'label_info'" class="detail-item-val">{{basicInfo[key]}}</span>
              <span v-if="key === 'collect_type'" class="detail-item-val">{{basicInfo[key]}}</span>
              <template v-if="key === 'plugin_display_name'">
                <template v-if="basicInfo && basicInfo.collect_type !== 'Log'">
                  <span class="detail-item-val plugin-id"
                        v-bk-tooltips.top="basicInfo['plugin_id'] + '(' + basicInfo[key] + ')'">
                    {{basicInfo['plugin_id'] + '(' + basicInfo[key] + ')'}}
                  </span>
                  <i
                    v-authority="{ active: !authority.PLUGIN_MANAGE_AUTH }"
                    class="icon-monitor icon-bianji col-name-icon"
                    style="margin-top: -4px;"
                    v-if="!input.show"
                    @click="handleToEditPlugin()"></i>
                </template>
                <span v-else>{{ basicInfo[key] }}</span>
              </template>
              <span v-if="key === 'period'" class="detail-item-val">{{basicInfo[key]}}s</span>
              <span v-if="key === 'update_user'" class="detail-item-val">{{basicInfo[key]}}</span>
              <span v-if="key === 'update_time'" class="detail-item-val">{{basicInfo[key]}}</span>
              <span v-if="key === 'bk_biz_id'" class="detail-item-val bizname">{{getBizName(basicInfo[key])}}</span>
              <div v-if="key === 'log_path' || key === 'filter_patterns'" class="detail-item-log">
                <template v-if="basicInfo[key].length">
                  <span v-for="(word, index) in basicInfo[key]" :key="index">{{ word }}</span>
                </template>
                <span v-else>--</span>
              </div>
              <span v-if="key === 'charset'" class="detail-item-val">{{basicInfo[key]}}</span>
              <div v-if="key === 'rules'" class="detail-item-log">
                <span v-for="(word, index) in basicInfo[key]" :key="index">{{ `${word.name}=${word.pattern}` }}</span>
              </div>
              <template v-if="basicInfo && basicInfo.collect_type === 'Process'">
                <span v-if="key === 'match'" class="detail-item-val process">
                  <template v-if="basicInfo[key] === 'command'">
                    <div class="match-title">{{ matchType[basicInfo[key]] }}</div>
                    <ul class="param-list">
                      <li class="param-list-item">
                        <span class="item-name">{{ $t('包含') }}</span>
                        <span class="item-content">{{ basicInfo.match_pattern}}</span>
                      </li>
                      <li class="param-list-item">
                        <span class="item-name">{{ $t('排除') }}</span>
                        <span class="item-content">{{ basicInfo.exclude_pattern }}</span>
                      </li>
                    </ul>
                  </template>
                  <template v-else>
                    <div class="match-title">{{ matchType[basicInfo[key]] }}</div>
                    <div>{{ `${$t('进程的pid绝对路径')}：${basicInfo.pid_path}` }}</div>
                  </template>
                </span>
                <span v-if="key === 'process_name'" class="detail-item-val">{{basicInfo[key]}}</span>
                <span v-if="key === 'port_detect'" class="detail-item-val">{{basicInfo[key]}}</span>
              </template>
            </li>
          </ul>
          <div class="param-label" v-if="runtimeParams.length"> {{ $t('运行参数：') }} </div>
          <ul class="param-list" v-if="runtimeParams.length">
            <li class="param-list-item" v-for="(item, index) in runtimeParams" :key="index">
              <span class="item-name">{{item.name}}</span>
              <span class="item-content" v-if="['password', 'encrypt'].includes(item.type)">******</span>
              <span class="item-content" v-else>{{(item.type === 'file' ? item.value.filename : item.value ) || '--'}}</span>
            </li>
          </ul>
          <div class="metric-label" :style="{ marginTop: runtimeParams.length ? '24px' : '14px' }"> {{ $t('指标预览：') }} </div>
          <right-panel class="metric-wrap"
                       need-border
                       v-for="(table, index) in metricList"
                       @change="handleCollapseChange(index)"
                       :key="index"
                       :class="{ 'no-bottom': table.collapse }"
                       :collapse="table.collapse">
            <div slot="title" class="metric-wrap-title">
              {{ getTitle(table) }}</div>
            <bk-table class="metric-wrap-table" :data="table.list" :empty-text="$t('查询无数据')">
              <bk-table-column :label="$t('指标/维度')" width="150">
                <template slot-scope="scope">
                  {{scope.row.metric === 'metric' ? $t('指标（Metric）') : $t('维度（Dimension）')}}
                </template>
              </bk-table-column>
              <bk-table-column :label="$t('英文名')" min-width="150">
                <template slot-scope="scope">
                  <span :title="scope.row.englishName">{{scope.row.englishName || '--'}}</span>
                </template>
              </bk-table-column>
              <bk-table-column :label="$t('别名')" min-width="150">
                <template slot-scope="scope">
                  <span :title="scope.row.aliaName">{{scope.row.aliaName || '--'}}</span>
                </template>
              </bk-table-column>
              <bk-table-column :label="$t('类型')" width="80">
                <template slot-scope="scope">
                  <span :title="scope.row.type">{{scope.row.type || '--'}}</span>
                </template>
              </bk-table-column>
              <bk-table-column :label="$t('单位')" width="100">
                <template slot-scope="scope">
                  <span :title="scope.row.unit">{{scope.row.unit || '--'}}</span>
                </template>
              </bk-table-column>
            </bk-table>
          </right-panel>
        </div>
        <div class="collect-target" v-show="active === 1">
          <!-- <right-panel need-border> -->
          <bk-table :data="targetInfo.table_data" :empty-text="$t('查询无数据')"
                    v-if="['TOPO', 'SET_TEMPLATE', 'SERVICE_TEMPLATE'].includes(targetInfo.target_node_type)">
            <bk-table-column :label="$t('节点名称')" width="140" prop="bk_inst_name">
            </bk-table-column>
            <bk-table-column :label="basicInfo.target_object_type === 'SERVICE' ? $t('当前实例数') : $t('当前主机数')" prop="count" width="100" align="right">
              <template slot-scope="scope">
                <div style="padding-right: 10px;">{{ scope.row.count }}</div>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('分类')" min-width="150">
              <template slot-scope="scope">
                <template v-if="scope.row.labels.length">
                  <span v-for="(item, index) in scope.row.labels"
                        :key="index"
                        class="classifiy-label">
                    <span class="label-name">{{item.first}}</span>
                    <span class="label-name">{{item.second}}</span>
                  </span>
                </template>
                <span v-else>--</span>
              </template>
            </bk-table-column>
          </bk-table>
          <bk-table :data="targetInfo.table_data" :empty-text="$t('查询无数据')" v-else-if="targetInfo.target_node_type === 'INSTANCE'">
            <bk-table-column label="IP" width="140" prop="ip">
            </bk-table-column>
            <bk-table-column :label="$t('Agent状态')" prop="agent_status" width="100">
              <template slot-scope="scope">
                <span :style="{ color: scope.row.agent_status === 'normal' ? '#2DCB56' : '#EA3636' }">{{scope.row.agent_status === 'normal' ? $t('正常') : $t('异常')}}</span>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('云区域')" min-width="150">
              <template slot-scope="scope">
                <span :title="scope.row.bk_cloud_name">{{scope.row.bk_cloud_name || '--'}}</span>
              </template>
            </bk-table-column>
          </bk-table>
          <!-- </right-panel> -->
        </div>
      </div>
    </div>
  </bk-sideslider>
</template>
<script>
import RightPanel from '../../../components/ip-select/right-panel'
import { frontendCollectConfigDetail, renameCollectConfig } from '../../../../monitor-api/modules/collecting'
import { PLUGIN_MANAGE_AUTH } from '../authority-map'
export default {
  name: 'CollectorConfigDetail',
  components: {
    RightPanel
  },
  props: {
    sideData: {
      type: Object,
      default() {
        return {}
      }
    },
    sideShow: Boolean
  },
  inject: ['authority', 'handleShowAuthorityDetail'],
  data() {
    return {
      active: 0,
      loading: false,
      basicInfo: null,
      metricList: [],
      runtimeParams: [],
      targetInfo: {},
      basicInfoMap: {
        name: this.$t('配置名称'),
        id: 'ID',
        label_info: this.$t('对象'),
        collect_type: this.$t('采集方式'),
        plugin_display_name: this.$t('插件'),
        period: this.$t('采集周期'),
        update_user: this.$t('操作者'),
        update_time: this.$t('操作时间'),
        bk_biz_id: this.$t('所属')
      },
      input: {
        show: false,
        copyName: ''
      },
      name: '',
      matchType: {
        command: this.$t('命令行匹配'),
        pid: this.$t('pid文件')
      }
    }
  },
  computed: {
    bizList() {
      return this.$store.getters.bizList
    }
  },
  // watch: {
  //     sideShow: {
  //         handler (v) {
  //             if (v) {
  //                 this.getDetailData()
  //             } else {
  //                 this.name = ''
  //             }
  //         }
  //     }
  // },
  created() {
    this.getDetailData()
  },
  beforeDestroy() {
    this.handleHidden()
  },
  methods: {
    getBizName(id) {
      const item = this.bizList.find(i => i.id === id) || {}
      return item.text || '--'
    },
    getDetailData() {
      this.loading = true
      frontendCollectConfigDetail({ id: this.sideData.id }, { needMessage: true }).then((data) => {
        const sideDataId = { id: this.sideData.id }
        this.basicInfo = { ...data.basic_info, ...sideDataId }
        if (data.extend_info.log) {
          this.basicInfo = { ...this.basicInfo, ...data.extend_info.log }
          !this.basicInfo.filter_patterns && (this.basicInfo.filter_patterns = [])
          this.basicInfoMap = {
            ...this.basicInfoMap,
            log_path: this.$t('日志路径'),
            filter_patterns: this.$t('排除规则'),
            rules: this.$t('关键字规则'),
            charset: this.$t('日志字符集')
          }
        }
        if (data.extend_info.process) {
          const { process } = data.extend_info
          this.basicInfoMap = {
            ...this.basicInfoMap,
            match: this.$t('进程匹配'),
            process_name: this.$t('进程名'),
            port_detect: this.$t('端口探测')
          }
          const { match_type: matchType, process_name: processName, port_detect: portDetect,
            match_pattern: matchPattern, exclude_pattern: excludePattern, pid_path: pidPath } = process
          this.basicInfo = {
            ...this.basicInfo,
            match: matchType,
            match_pattern: matchPattern,
            exclude_pattern: excludePattern,
            pid_path: pidPath,
            process_name: processName || '--',
            port_detect: `${portDetect}`
          }
        }
        data.metric_list.forEach((item, index) => {
          item.collapse = index === 0
        })
        this.metricList = data.metric_list
        this.runtimeParams = data.runtime_params
        this.targetInfo = data.target_info
        this.input.copyName = data.basic_info.name
        this.name = data.basic_info.name
      })
        .catch((err) => {
          this.$bkMessage({
            theme: 'error',
            message: err.message || this.$t('获取数据出错了')
          })
          this.$emit('set-hide', false)
        })
        .finally(() => {
          this.loading = false
        })
    },
    handleHidden() {
      this.name = ''
      this.$emit('set-hide', false)
    },
    handleCollapseChange(v) {
      this.metricList.forEach((item, index) => {
        if (index === v) {
          item.collapse = !item.collapse
        } else {
          item.collapse = false
        }
      })
    },
    handleLabelKey(v, e) {
      if (e.code === 'Enter' || e.code === 'NumpadEnter') {
        this.handleTagClickout()
      }
    },
    handleTagClickout() {
      const data = this.basicInfo
      const { copyName } = this.input
      if (copyName.length && copyName !== data.name) {
        this.handleUpdateConfigName(data, copyName)
      } else {
        data.copyName = data.name
        this.input.show = false
      }
    },
    handleEditLabel(key) {
      this.input.show = true
      this.$nextTick().then(() => {
        this.$refs[`input${key}`][0].focus()
      })
    },
    handleUpdateConfigName(data, copyName) {
      this.loading = true
      renameCollectConfig({ id: data.id, name: copyName }, { needMessage: false }).then(() => {
        this.basicInfo.name = copyName
        this.name = copyName
        this.$emit('update-name', data.id, copyName)
        this.$bkMessage({
          theme: 'success',
          message: this.$t('修改成功')
        })
      })
        .catch((err) => {
          this.$bkMessage({
            theme: 'error',
            message: err.message || this.$t('发生错误了')
          })
        })
        .finally(() => {
          this.input.show = false
          this.loading = false
        })
    },
    handleToEditPlugin() {
      if (!this.authority.PLUGIN_MANAGE_AUTH) {
        this.handleShowAuthorityDetail(PLUGIN_MANAGE_AUTH)
      } else {
        this.$emit('edit-plugin', this.basicInfo)
      }
    },
    handleToEdit() {
      this.$emit('edit', this.basicInfo.id)
    },
    getTitle(table) {
      if (this.$i18n.locale !== 'enUS') {
        return `${table.id}（${table.name}）`
      }
      return table.id
    }
  }
}
</script>
<style lang="scss" scoped>
.collector-config-detail {
  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-right: 40px;
    &-title {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
  .detail-content {
    padding: 18px 30px;
    background: #fff;
    font-size: 12px;
    color: #63656e;
    height: calc(100vh - 80px);
    overflow: auto;
    &-tab {
      display: flex;
      height: 36px;
      align-items: center;
      border-bottom: 1px solid #dcdee5;
      font-size: 12px;
      color: #63656e;
      .tab-item {
        flex: 0 0 auto;
        height: 36px;
        min-width: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        border-bottom: 2px solid transparent;
        &.tab-active {
          color: #3a84ff;
          border-bottom-color: #3a84ff;
        }
      }
    }
    &-wrap {
      padding-top: 17px;
      .basic-info {
        &-detail {
          overflow: hidden;
          .detail-item {
            display: flex;
            align-items: flex-start;
            width: 100%;
            float: left;
            margin-bottom: 10px;
            min-height: 20px;
            &-val {
              padding-top: 2px;
              .name-wrapper {
                display: flex;
                align-items: flex-start;
                width: 210px;
              }
              .config-name {
                max-width: calc(100% - 24px);
                overflow: hidden;
                display: inline-block;
                text-overflow: ellipsis;
                white-space: nowrap;
              }
              &.bizname {
                margin-top: -2px;
              }
              &.process {
                display: block;
                width: 100%;
                margin-top: -2px;
                .match-title {
                  margin-bottom: 10px;
                }
              }
            }
            &-log {
              display: flex;
              flex-direction: column;
            }
            &-label {
              color: #979ba5;
              min-width: 86px;
              display: inline-block;
              text-align: right;
              margin-right: 14px;
            }
            &:last-child::after {
              content: " ";
              zoom: 1;
              clear: both;
            }
            &-name {
              padding-top: 10px;
            }
          }
          .plugin-id {
            text-overflow: ellipsis;
            overflow: hidden;
            white-space: nowrap;
          }
          .col-name-icon {
            color: #dcdee5;
            font-size: 24px;
            &:hover {
              color: #3a84ff;
              cursor: pointer;
            }
          }
        }
        .param-label,
        %param-label {
          color: #979ba5;
          margin: 14px 0 10px;
        }
        .param-list {
          border: 1px solid #dcdee5;
          border-radius: 2px;
          &-item {
            display: flex;
            align-items: center;
            &:not(:last-child) {
              border-bottom: 1px solid #dcdee5;
            }
            .item-name {
              width: 50%;
              height: 30px;
              line-height: 32px;
              color: #979ba5;
              padding-left: 20px;
              border-right: 1px solid #dcdee5;
              background: #fafbfd;
            }
            .item-content {
              width: 50%;
              padding-left: 20px;
            }
          }
        }
        .metric-label {
          margin-top: 24px;

          @extend %param-label;
        }
        .metric-wrap {
          margin-bottom: 10px;
          &.no-bottom {
            border-bottom: 0;
          }
          &-title {
            line-height: 14px;
          }
        }
      }
      .collect-target {
        .classifiy-label {
          border: 1px solid #dcdee5;
          border-radius: 2px;
          background: #fafbfd;
          font-size: 12px;
          display: inline-block;
          margin: 3px;
          .label-name {
            display: inline-block;
            height: 24px;
            line-height: 24px;
            padding: 0 7px;
            text-align: center;
            &:first-child {
              border-right: 1px solid #dcdee5;
              background: #fff;
            }
          }
        }
      }
    }
  }
}
</style>

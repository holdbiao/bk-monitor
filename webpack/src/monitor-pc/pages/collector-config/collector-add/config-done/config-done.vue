<template>
  <div class="done">
    <done :options="options">
      <template v-slot:text>
        <div v-if="nodeType === 'INSTANCE'">
          <span class="text"> {{ $t('共成功') }} {{options.type}} {{ $t('了') }} <span class="num success">{{options.successTotal}}</span> {{suffixName}}</span>
          <span class="text">,{{ $t('失败') }} <span class="num fail">{{options.failTotal}}</span> {{suffixName}}</span>
        </div>
        <div v-else>
          <span class="text"> {{ $t('共成功') }} {{options.type}} {{ $t('了') }} <span class="num">{{hosts.contents.length}}</span> {{ $t('个节点内的') }} <span class="num success">{{options.successTotal}}</span> {{suffixName}}</span>
          <span class="text">,{{ $t('失败') }} <span class="num fail">{{options.failTotal}}</span> {{suffixName}}</span>
        </div>
      </template>
      <template v-slot:footer>
        <bk-button v-if="config.data && config.data.id" theme="primary" @click="handleGoConfigView">{{ $t('检查视图') }}</bk-button>
        <bk-button
          v-authority="{ active: !authority.STRATEGY_VIEW_AUTH }"
          theme="primary"
          @click="authority.STRATEGY_VIEW_AUTH ? handleGoStrategy() : handleShowAuthorityDetail(collectAuth.STRATEGY_VIEW_AUTH)">
          {{ $t('策略配置') }}
        </bk-button>
        <!-- <bk-button theme="primary" v-if="false"> {{ $t('视图配置') }} </bk-button> -->
        <bk-button @click="close"> {{ $t('关闭') }} </bk-button>
      </template>
    </done>
  </div>
</template>
<script>
import Done from './loading-done'
export default {
  name: 'stop-done',
  components: {
    Done
  },
  inject: ['authority', 'handleShowAuthorityDetail', 'collectAuth'],
  props: {
    data: {
      type: Object,
      default: () => ({})
    },
    hosts: {
      type: Object,
      default: () => ({
        config_info: {},
        contents: [],
        headerData: {}
      })
    },
    type: {
      type: String,
      default: 'ADD'
    },
    config: {
      type: Object,
      default() {
        return {}
      }
    }
  },
  data() {
    return {
      options: {
        loading: false,
        status: true,
        title: this.$t('配置已停用'),
        text: '',
        type: '',
        successTotal: 0,
        failTotal: 0
      },
      nodeType: 'INSTANCE'
    }
  },
  computed: {
    suffixName() {
      return this.hosts.config_info.target_object_type === 'HOST' ? this.$t('台主机') : this.$t('个实例')
    }
  },
  created() {
    const type = {
      STOPPED: this.$t('启用'),
      STARTED: this.$t('停用'),
      UPGRADE: this.$t('升级'),
      CREATE: this.$t('新增'),
      ADD: this.$t('新增'),
      EDIT: this.$t('编辑'),
      ROLLBACK: this.$t('回滚')
    }
    this.options.type = type[this.type]
    this.options.title = `${this.$t('配置已')}${type[this.type]}`
    this.nodeType = this.data.nodeType
    this.options.successTotal = this.hosts.headerData.successNum
    this.options.failTotal = this.hosts.headerData.failedNum
  },
  methods: {
    close() {
      // this.$router.back()
      this.$router.push({
        name: 'collect-config'
      })
    },
    handleGoStrategy() {
      const setData = this.config.set.data
      this.$router.push({
        name: 'strategy-config-add',
        params: {
          objectId: setData.objectId,
          strategyName: setData.name
        }
      })
    },
    // 点击检查视图跳转
    handleGoConfigView() {
      if (this.config.data.id) {
        this.$router.push({
          name: 'collect-config-view',
          params: {
            id: this.config.data.id
          }
        })
      }
    }
  }
}
</script>
<style lang="scss" scoped>
.done {
  padding-top: 84px;
  /deep/ .bk-button {
    margin-right: 10px;
  }
  .text {
    color: #63656e;
  }
  .num {
    color: #3a84ff;
  }
  .success {
    color: #2dcb56;
  }
  .fail {
    color: #ea3636;
  }
}
</style>

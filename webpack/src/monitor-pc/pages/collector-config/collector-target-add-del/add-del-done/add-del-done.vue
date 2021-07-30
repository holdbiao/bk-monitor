<template>
  <div class="done">
    <done :options="options">
      <template v-slot:text>
        <div class="success-container">
          <p> {{ $t('对该配置') }} {{textMap[type]}}， {{ $t('成功') }} <span class="success-total"> {{successTotal}} </span>
            {{data.objectTypeEn === 'HOST' ? $t('台主机') + ',' : $t('个实例') + ','}} {{ $t('失败') }} <span class="fail-total"> {{failTotal}} </span>
            {{data.objectTypeEn === 'HOST' ? $t('台主机') : $t('个实例')}}
          </p>
        </div>
      </template>
      <template v-slot:footer>
        <bk-button key="123" theme="primary" @click="handleGoStrategy"> {{ $t('策略配置') }} </bk-button>
        <!-- <bk-button theme="primary" v-if="false"> {{ $t('视图配置') }} </bk-button> -->
        <bk-button @click="handleClose"> {{ $t('关闭') }} </bk-button>
      </template>
    </done>
  </div>
</template>
<script>
import Done from '../../collector-add/config-done/loading-done'
export default {
  name: 'add-del-done',
  components: {
    Done
  },
  props: {
    data: {
      type: Object,
      default: () => ({
        config_info: {},
        headerData: {},
        contents: []
      })
    },
    config: Object,
    step: {
      type: Number,
      default: 2
    },
    type: {
      type: String,
      default: 'ADD_DEL'
    },
    hosts: {
      type: Object,
      default: () => ({})
    },
    diffData: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      options: {
        loading: false,
        status: true,
        title: this.$t('操作完成'),
        text: ''
      },
      textMap: {
        ROLLBACK: this.$t('增/删目标'),
        ADD_DEL: this.$t('增/删目标'),
        EDIT: this.$t('编辑')
      },
      isCloseOut: false,
      successTotal: 0,
      failTotal: 0
    }
  },
  created() {
    this.successTotal = this.hosts.headerData.successNum
    this.failTotal = this.hosts.headerData.failedNum
  },
  methods: {
    handleClose() {
      this.$router.push({
        name: 'collect-config'
      })
    },
    handleGoStrategy() {
      this.$router.push({
        name: 'strategy-config-add',
        params: {
          objectId: this.config.params.label,
          strategyName: this.config.params.name
        }
      })
    }
  }
}
</script>
<style lang="scss" scoped>
.done {
    padding-top: 80px;
    .success-total {
        color: #2DCB56;
    }
    .fail-total {
        color: #EA3636;
    }
    /deep/ .bk-button {
        margin-right: 10px;
    }
}
</style>

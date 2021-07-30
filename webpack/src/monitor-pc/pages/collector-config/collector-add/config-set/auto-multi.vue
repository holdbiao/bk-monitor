<template>
  <div>
    <div class="auto-multi" v-for="(items,indexs) in souceDataInfo" :key="indexs">
      <div class="del-icon" @click="delAuth(indexs)">
        <bk-icon type="close" />
      </div>
      <template v-for="(item,index) in items">
        <template v-if="item.auth_priv">
          <verify-input
            v-if="item.auth_priv[curAuthPriv[indexs].curAuthPriv] && item.auth_priv[curAuthPriv[indexs].curAuthPriv].need"
            class="param-item"
            :key="index"
            :show-validate.sync="item.validate.isValidate"
            :validator="item.validate"
            position="right"
          >
            <auto-complete-input
              class="reset-big-width"
              :tips-data="tipsData"
              :type="item.type"
              :config="item"
              :cur-auth-priv="curAuthPriv[indexs].curAuthPriv"
              @autoHandle="autoHandle"
              v-model.trim="item.default"
              @blur="handleParamValidate(item)"
            >
              <template slot="prepend">
                <bk-popover placement="top" :tippy-options="tippyOptions">
                  <div class="prepend-text">
                    {{ item.description ? item.description : item.name }}
                  </div>
                  <div slot="content">
                    <div>{{ $t("参数名称：") }} {{ item.name }}</div>
                    <div>{{ $t("参数类型：") }} {{ paramType[item.mode] }}</div>
                    <div>{{ $t("参数说明：") }} {{ item.description || "--" }}</div>
                  </div>
                </bk-popover>
              </template>
            </auto-complete-input>
          </verify-input>
        </template>
        <template v-else>
          <verify-input class="param-item"
                        :key="index"
                        :show-validate.sync="item.validate.isValidate"
                        :validator="item.validate"
                        position="right">
            <!-- 自动补全 -->
            <auto-complete-input
              class="reset-big-width"
              :tips-data="tipsData"
              :type="item.type"
              :config="item"
              @autoHandle="autoHandle"
              v-model.trim="item.default"
              @curAuthPriv="handleAuthPriv(...arguments, indexs)"
              @blur="handleParamValidate(item)">
              <template slot="prepend">
                <bk-popover placement="top" :tippy-options="tippyOptions">
                  <div class="prepend-text">{{ item.description ? item.description : item.name }}</div>
                  <div slot="content">
                    <div> {{ $t('参数名称：') }} {{ item.name }}</div>
                    <div> {{ $t('参数类型：') }} {{ paramType[item.mode] }}</div>
                    <div> {{ $t('参数说明：') }} {{ item.description || '--' }}</div>
                  </div>
                </bk-popover>
              </template>
            </auto-complete-input>
          </verify-input>
        </template>
      </template>
    </div>
    <div class="auto-multi" v-if="allowAdd">
      <div class="add-btn" @click="addAuth">新增用户配置</div>
    </div>
  </div>
</template>
<script>
import AutoCompleteInput from './auto-complete-input'
import VerifyInput from '../../../plugin-manager/plugin-instance/set-steps/verify-input'
import * as snmp from './snmp'
import { bkIcon } from 'bk-magic-vue'
import { deepClone } from '../../../../../monitor-common/utils/utils'
export default {
  name: 'AutoMulti',
  components: {
    AutoCompleteInput,
    VerifyInput,
    bkIcon
  },
  props: {
    templateData: {
      type: Array,
      default: () => []
    },
    souceData: {
      type: Array,
      default: []
    },
    tipsData: {
      type: Array,
      default: []
    },
    paramType: {
      type: Object,
      default: {}
    },
    allowAdd: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      tippyOptions: {
        distance: 0
      },
      curAuthPriv: [],
      souceDataInfo: [],
      templateDataInfo: [],
      isCanSave: false
    }
  },
  watch: {
    souceData: {
      handler: 'handleSouceData',
      immediate: true
    }
  },
  created() {
    this.souceData.forEach((item) => {
      item.forEach((value) => {
        if (value.key === 'security_level') {
          this.curAuthPriv.push({ curAuthPriv: value.default })
        }
      })
    })
    this.templateDataInfo = deepClone(this.templateData)
  },
  mounted() {
    this.trigger()
  },
  methods: {
    autoHandle() {
      this.trigger()
    },
    handleAuthPriv(v, index) {
      this.$set(this.curAuthPriv, index, { curAuthPriv: v })
      this.trigger()
    },
    handleSouceData(v) {
      this.souceDataInfo = deepClone(v)
    },
    addAuth() {
      this.curAuthPriv.push({ curAuthPriv: snmp.AuthPrivList[2] })
      this.souceDataInfo.push(deepClone(this.templateDataInfo))
      this.trigger()
    },
    delAuth(index) {
      if (this.souceDataInfo.length > 1) {
        this.curAuthPriv.splice(index, 1)
        this.souceDataInfo.splice(index, 1)
        this.trigger()
      }
    },
    trigger() {
      this.$emit('triggerData', this.souceDataInfo)
      this.isCanSave = this.authValidate()
      this.$emit('canSave', this.isCanSave)
    },
    authValidate() {
      let result = false
      const { excludeValidateMap } = snmp
      result = this.souceDataInfo.every((items, index) => items.every((item) => {
        if (!excludeValidateMap[this.curAuthPriv[index].curAuthPriv].includes(item.key)) {
          return item.type === 'file' ? item.default.value !==  '' : item.default !== ''
        }
        return true
      }))
      return result
    }
  }
}
</script>
<style lang="scss">
  .auto-multi {
    padding: 10px 20px 10px 10px;
    background: #fafbfd;
    position: relative;
    margin-bottom: 10px;
  }
  .reset-big-width {
    width: 490px;
  }
  .del-icon {
    position: absolute;
    top: 0;
    right: 0;
    font-size: 20px;
    cursor: pointer;
  }
  .add-btn {
    color: #3a84ff;
    cursor: pointer;
  }
</style>

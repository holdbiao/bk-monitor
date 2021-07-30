<template>
  <div class="advanced-option">
    <div class="advanced-form-item">
      <div class="item-label"> {{ $t('周期') }} </div>
      <div class="item-container cycle">
        <bk-select class="cycle-select" v-model="cycle.value" :clearable="false">
          <bk-option v-for="(time, index) in cycle.list" :key="index" :name="time.name" :id="time.id"></bk-option>
        </bk-select>
      </div>
    </div>
    <div class="advanced-form-item" v-show="isHttp">
      <div class="item-label"> {{ $t('期待返回码') }} </div>
      <div class="item-container code">
        <bk-input class="code-input" :placeholder="$t('HTTP请求返回码，如200，304，404等...')" v-model="response.code"></bk-input>
      </div>
    </div>
    <div class="advanced-form-item" v-if="!isIcmp">
      <div class="item-label"> {{ $t('期待响应信息') }} </div>
      <div class="item-container response">
        <bk-select @click.native="handleFocus(true)"
                   @toggle="handleFocus"
                   class="response-select"
                   :style="{ 'border-right-color': focusInput ? '#3c96ff' : focusSelect ? '#3a84ff' : '#c4c6cc' }"
                   v-model="response.relation.value"
                   :clearable="false">
          <bk-option v-for="(item, index) in response.relation.list" :key="index" :id="item.id" :name="item.name"></bk-option>
        </bk-select>
        <bk-input @focus="handleFocusInput" @blur="focusInput = false" :class="['response-input', focusSelect ? 'hide-border' : '']" :placeholder="$t('通过指定匹配内容来检查响应是否正确，为空则不做匹配检查')" v-model="response.message"></bk-input>
        <div class="hint-icon" v-bk-tooltips.top="$t('系统会自动创建该告警策略，响应信息匹配失败将会产生告警。')">
          <span class="icon-monitor icon-tips"></span>
        </div>
      </div>
    </div>
    <div class="advanced-form-item" v-show="isHttp">
      <div class="item-label"> {{ $t('SSL证书校验') }} </div>
      <div class="item-container">
        <bk-radio-group v-model="isSSL">
          <bk-radio :value="true">{{ $t('是') }}</bk-radio>
          <bk-radio :value="false">{{ $t('否') }}</bk-radio>
        </bk-radio-group>
      </div>
    </div>
    <div class="advanced-form-item" v-if="!isIcmp">
      <div class="item-label"> {{ $t('地理位置') }} </div>
      <div class="item-container location">
        <bk-select class="location-select" v-model="location.value" searchable>
          <bk-option style="width: 212px" v-for="(item, index) in location.list" :key="index" :id="item.cn" :name="item.cn"></bk-option>
        </bk-select>
        <bk-select v-show="citys.length" class="location-select" v-model="location.city">
          <bk-option style="width: 212px" v-for="(city, index) in citys" :key="index" :id="city.cn" :name="city.cn"></bk-option>
        </bk-select>
      </div>
    </div>
    <div :class="['advanced-form-item', headers.length > 1 ? 'headers' : '']" v-show="isHttp">
      <div class="item-label"> {{ $t('头信息') }} </div>
      <div class="item-container">
        <div :class="['item-header', headers.length > 1 ? 'item-bottom' : '']" v-for="(item, index) in headers" :key="index">
          <bk-select class="header-select" v-model="item.name">
            <bk-option style="width: 218px;" v-for="(header, headerIndex) in item.list" :key="headerIndex" :id="header" :name="header"></bk-option>
          </bk-select>
          <bk-input class="header-input" v-model="item.value"></bk-input>
          <div class="operation">
            <span class="bk-icon icon-plus-circle" @click="addHttpHeader"></span>
            <span v-show="headers.length > 1" class="bk-icon icon-minus-circle" @click="removeHttpHeader(index)"></span>
          </div>
        </div>
      </div>
    </div>
    <template v-if="isIcmp">
      <div class="advanced-form-item">
        <div class="item-label"> {{ $t('周期内连续探测') }} </div>
        <div class="item-container response">
          <bk-input type="number" :min="1" :max="20" v-model="response.totalNum" style="width: 160px;"></bk-input>
        </div>
      </div>
      <div class="advanced-form-item">
        <div class="item-label"> {{ $t('探测包大小') }} </div>
        <div class="item-container response">
          <bk-input type="number" :min="24" :max="65507" v-model="response.size" style="width: 160px;"></bk-input>
        </div>
      </div>
    </template>
  </div>
</template>
<script>
import { getHttpHeaders } from '../../../../../monitor-api/modules/uptime_check'
import { countryList } from '../../../../../monitor-api/modules/commons'
export default {
  name: 'advanced-option',
  props: {
    protocol: {
      type: String,
      default: 'HTTP'
    },
    options: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      focusSelect: false,
      focusInput: false,
      cycle: {
        list: [
          {
            id: 1,
            name: this.$t('1分钟')
          },
          {
            id: 5,
            name: this.$t('5分钟')
          }
        ],
        value: 1
      },
      response: {
        code: '',
        message: '',
        size: 68,
        totalNum: 3,
        relation: {
          list: [
            {
              id: 'in',
              name: this.$t('包含')
            },
            {
              id: 'nin',
              name: this.$t('不包含')
            },
            {
              id: 'reg',
              name: this.$t('正则')
            }
          ],
          value: 'nin'
        }
      },
      isSSL: false,
      location: {
        list: [],
        value: '',
        city: ''
      },
      headers: [
        {
          list: [],
          name: '',
          value: ''
        }
      ]
    }
  },
  computed: {
    citys() {
      const country = this.location.list.find(item => item.cn === this.location.value)
      if (country?.children.length) {
        return country.children
      }
      return []
    },
    isHttp() {
      return this.protocol === 'HTTP'
    },
    isIcmp() {
      return this.protocol === 'ICMP'
    }
  },
  watch: {
    options: {
      handler(val) {
        this.setAdvancedOptionsData(val)
      },
      deep: true
    }
  },
  created() {
    this.getHttpHeaders()
    this.getLocation()
  },
  methods: {
    handleFocus(val) {
      this.focusSelect = val
      this.focusInput = false
    },
    handleFocusInput() {
      this.focusSelect = false
      this.focusInput = true
    },
    getHttpHeaders() {
      getHttpHeaders().then((data) => {
        this.headers[0].list = data
      })
    },
    getLocation() {
      countryList().then((data) => {
        if (data.length) {
          this.location.list = data
        }
      })
      // .fail(() => {
      //     this.$bkMessage({
      //         theme: 'error',
      //         message: '获取地理位置数据失败'
      //     })
      // })
    },
    addHttpHeader() {
      const header = JSON.parse(JSON.stringify(this.headers[0].list))
      this.headers.push({
        list: header,
        name: '',
        value: ''
      })
    },
    removeHttpHeader(index) {
      this.headers.splice(index, 1)
    },
    getValue() {
      const headers = JSON.parse(JSON.stringify(this.headers))
      const header = headers[0].name && headers[0].value
        ? headers.map(item => ({ name: item.name, value: item.value }))
        : []
      const { response } = this
      return {
        total_num: response.totalNum,
        size: response.size,
        period: this.cycle.value,
        response_code: response.code.trim(),
        response: response.message || null,
        response_format: response.relation.value,
        insecure_skip_verify: this.isSSL,
        headers: header,
        location: { bk_state_name: this.location.value, bk_province_name: this.location.city }
      }
    },
    setAdvancedOptionsData(data) {
      this.cycle.value = data.period || 1
      this.response.code = data.response_code || ''
      this.response.relation.value = data.response_format || 'nin'
      this.response.message = data.response || ''
      this.response.totalNum = data.total_num || 3
      this.response.size = data.size || 68
      this.isSSL = Boolean(data.insecure_skip_verify)
      if (!this.isIcmp) {
        try {
          const { headers } = data
          const headerTemplate = JSON.parse(JSON.stringify(this.headers[0]))
          headers.forEach((item, index) => {
            if (!this.headers[index]) {
              this.headers.push(headerTemplate)
            }
            this.headers[index].name = item.name
            this.headers[index].value = item.value
          })
        } catch (error) {
          console.error(error)
        }
        this.location.value = data.location.bk_state_name
        this.location.city = data.location.bk_province_name
      }
    },
    setDefaultData() {
      this.cycle.value = 1
      this.response.code = ''
      this.response.message = ''
      this.isSSL = true
      this.response.relation.value = 'nin'
      this.location.city = ''
      this.location.value = ''
      this.response.size = 68
      this.response.totalNum = 3
      this.headers = [
        {
          list: [],
          name: '',
          value: ''
        }
      ]
      this.getHttpHeaders()
    }
  }
}
</script>
<style lang="scss" scoped>
@mixin hint-icon {
  width: 18px;
  height: 18px;
  line-height: 18px;
  display: inline-block;
  fill: #fff;
  margin-left: 10px;
  cursor: pointer;
  font-size: 16px;
}

.advanced-option {
  width: 100%;
  .advanced-form-item {
    display: flex;
    flex-direction: row;
    align-items: center;
    margin-bottom: 20px;
    color: #63656e;
    &.headers {
      align-items: start;
    }
    .item-label {
      flex: 0 0 102px;
      margin-right: 15px;
      text-align: right;
      font-size: 14px;
    }
    .item-container {
      &.response {
        display: inline-flex;
        align-items: center;
        .response-select {
          width: 94px;
          border-radius: 2px 0 0 2px;
        }
        .response-input {
          width: 409px;
          /deep/ .bk-form-input {
            border-radius: 0 2px 2px 0;
            border-left: 0;
          }
        }
        .hint-icon {
          @include hint-icon();
        }
      }
      .item-label {
        flex: 0 0 100px;
        margin-right: 15px;
        text-align: right;
        font-size: 14px;
      }
      .icon-tips:hover {
        color: #3a84ff;
      }
      .item-header {
        display: flex;
        .operation {
          width: 42px;
          display: inline-flex;
          align-items: center;
          justify-content: space-between;
          .bk-icon {
            font-size: 18px;
            cursor: pointer;
          }
        }
        &.item-bottom {
          margin-bottom: 10px;
        }
        .header-select,
        .header-input {
          width: 220px;
          margin-right: 10px;
        }
      }
      /deep/ .bk-form-radio {
        margin-right: 62px;
        margin-bottom: 0;
        .icon-check {
          &::before {
            content: none;
          }
        }
      }
      /deep/ .bk-select {
        background-color: #fff;
      }
      &.location {
        display: inline-flex;
        align-items: center;
        .location-select {
          width: 218px;
          &:first-child {
            margin-right: 10px;
          }
        }
        .hint-icon {
          @include hint-icon();
        }
      }
      .code-input {
        width: 503px;
      }
      .cycle-select {
        width: 160px;
      }
    }
  }
}
</style>

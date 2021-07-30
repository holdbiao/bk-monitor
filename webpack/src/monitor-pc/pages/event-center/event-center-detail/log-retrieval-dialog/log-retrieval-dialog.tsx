import { Component as tsc } from 'vue-tsx-support'
import { Component, Emit, Prop, Ref, Watch } from 'vue-property-decorator'
import { Dialog, Form, FormItem, Select, Option, DatePicker, Input, Button } from 'bk-magic-vue'
import './log-retrieval-dialog.scss'
import moment from 'moment'
/* eslint-disable camelcase */

interface LogRetrievalDialogProps {
  show: boolean,
  indexList: Array<indexItem>,
  showTips: boolean,
  ip: string
}
interface LogRetrievalDialogEvent {
  onShowChange: boolean;
}
interface indexItem {
  collector_config_id?: number,
  collector_config_name?: string,
  collector_scenario_id?: string,
  index_set_id?: number
}

@Component({
  name: 'LogRetrievalDialog'
})
export default class LogRetrievalDialog extends tsc<LogRetrievalDialogProps, LogRetrievalDialogEvent> {
  @Prop({ type: Boolean, default: false }) show: boolean
  @Prop({ type: Boolean, default: false }) showTips: boolean
  @Prop({ type: Array, default: () => ([]) }) indexList: Array<indexItem>
  @Prop({ type: String, default: '' }) ip: string
  @Ref('logForm') refForm

  public dialog = {
    headerPosition: 'left',
    okText: window.i18n.t('确定'),
    cancelText: window.i18n.t('取消'),
    width: 571,
    title: window.i18n.t('日志检索'),
    autoClose: false
  }
  public data = {
    indexSet: '',
    time: ['', ''],
    sql: ''
  }
  public indexSetList = []
  public rules = {
    indexSet: [{
      required: true,
      message: window.i18n.t('必填项'),
      trigger: 'blur'
    }],
    time: [{
      validator: () => this.data.time[0] !== '',
      message: window.i18n.t('必填项'),
      trigger: 'blur'
    }],
    sql: [{
      required: true,
      message: window.i18n.t('必填项'),
      trigger: 'blur'
    }]
  }

  @Watch('show')
  handleShow(v) {
    if (v) {
      this.refForm.clearError()
      this.indexSetList = this.indexList.map(item => ({ id: item.index_set_id, name: item.collector_config_name }))
      if (this.indexSetList.length) {
        this.data.indexSet = this.indexSetList[0].id
      }
    }
  }

  @Emit('showChange')
  showChange(v) {
    return v
  }

  confirm() {
    this.refForm.validate().then(() => {
      // 验证成功
      const startTime = encodeURIComponent(moment(this.data.time[0]).format('YYYY-MM-DD HH:mm:ss'))
      const endTime = encodeURIComponent(moment(this.data.time[1]).format('YYYY-MM-DD HH:mm:ss'))
      const host = window.bk_log_search_url || window.bklogsearch_host
      const url = `${host}#/retrieve/${this.data.indexSet}?bizId=${this.$store.getters.bizId}&keyword=${encodeURIComponent(this.data.sql)}&start_time=${startTime}&end_time=${endTime}`
      window.open(url)
      this.showChange(false)
    }, () => {
      // 验证失败
    })
  }
  handleClose(v: boolean) {
    if (v) return
    this.showChange(v)
  }

  render() {
    return (
      <div>
        <Dialog
          value={this.show}
          header-position={this.dialog.headerPosition}
          ok-text={this.dialog.okText}
          cancel-text={this.dialog.cancelText}
          title={this.dialog.title}
          width={this.dialog.width}
          auto-close={this.dialog.autoClose}
          class="log-retrieval-dialog"
          on-confirm={this.confirm}
          {...{ on: { 'value-change': this.handleClose } }}
        >
          {this.showTips ? <div class="log-retrieval-tips">
            <div class="tips-top">
              <span class="icon-monitor icon-hint"></span>
              <span>{this.$t('提示：通过 {0} 未找到对应的索引集。如果要采集日志可以前往日志平台。', [this.ip])}</span>
            </div>
            <div class="tips-bottom">{this.$t('注意：ip查找索引集依赖节点管理版本>=2.1')}</div>
          </div> : undefined}
          <Form label-width={70}
            ref="logForm"
            {...{ props: {
              model: this.data,
              rules: this.rules
            } }}>
            <FormItem label={this.$t('索引集')} required={true} property='indexSet' error-display-type={'normal'}>
              <Select v-model={this.data.indexSet} searchable>
                {this.indexSetList.map(item => (
                  <Option key={item.id} id={item.id} name={item.name}></Option>
                ))}
              </Select>
            </FormItem>
            <FormItem label={this.$t('时间范围')} required={true} property={'time'} error-display-type={'normal'}>
              <DatePicker v-model={this.data.time} placeholder={this.$t('选择日期时间范围')} type={'datetimerange'}></DatePicker>
            </FormItem>
            <FormItem label={this.$t('查询语句')} required={true} property={'sql'} error-display-type={'normal'}>
              <Input
                placeholder={''}
                type={'textarea'}
                rows={3}
                maxlength={255}
                v-model={this.data.sql}>
              </Input>
            </FormItem>
          </Form>
          <template slot="footer">
            <Button on-click={this.confirm} disabled={this.showTips} theme="primary" style="margin-right: 10px">{this.$t('确定')}</Button>
            <Button on-click={() => this.handleClose(false)}>{this.$t('取消')}</Button>
          </template>
        </Dialog>
      </div>
    )
  }
}

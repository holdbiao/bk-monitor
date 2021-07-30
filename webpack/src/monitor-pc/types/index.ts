import { Vue } from 'vue-property-decorator'

export interface IBaseEditor {
  [propsName: string]: any
}

export interface IMonacoEditorInstance extends IBaseEditor {
  updateOptions(params: any): void
  layout(params?: any): void
  getValue(params?: any): string
  setValue(params: string): void
  dispose(): void
  onContextMenu(params?: any): any
}

export default interface MonitorVue extends Vue {
  _l: any
  $bkMessage: any
  $bkPopover: any
  $bkInfo: any,
  $bus: any
}

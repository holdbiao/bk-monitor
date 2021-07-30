export interface ITreeItem {
  name: string,
  id: string,
  key: string,
  children?: ITreeItem[],
  parent?: ITreeItem,
  isCreate?: boolean,
  expanded?: boolean,
  renamed?: boolean,
  group?: string,
  groupName?: string
  parentKey?: string
}

export type TMode = 'create' | 'select'

export interface IAddWrapSize {
  width: number,
  height: number,
  startClientX: number,
  startClientY: number
}

export interface IList {
  labelName: string,
  id: string,
  children?: IList[],
  name?: string
}

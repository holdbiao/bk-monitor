import VueI18n from 'vue-i18n'

export interface IContent {
    [propName: string]: any;
}

export interface IConfig {
    label: string;
    span: number;
    prop: string;
}

export interface IOptions {
    text: VueI18n.TranslateResult;
    value: number;
}

export interface IDropdownMenu {
    value: number;
    options: IOptions[];
}

export interface ICompareData {
    current: number;
    max: number;
    avg: number;
    total: number;
    min: number;
    name: string;
}

export type CompareOptions = 'YESTERDAY' | 'WEEKLY'

export type CompareMap = {
    [p in CompareOptions]: VueI18n.TranslateResult;
}

export interface ISelectGroup {
    list: ISelectItem[];
    active: number;
}

export interface ISeriesData {
    name: string;
    data: Array<{}>;
}

export interface ISelectItem {
    text: VueI18n.TranslateResult;
    value: number;
}

export interface ICompare {
    type: string;
    value: number;
}

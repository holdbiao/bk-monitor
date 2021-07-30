import VueI18n from 'vue-i18n'

export interface IHeaderItem {
    id: 'alarmDate' | 'message' | 'bkBizName';
    value: string;
    title: VueI18n.TranslateResult;
}

export interface IHeader {
    list: IHeaderItem[];
    active: string[];
}

export interface IEventItem {
    status: keyof IStatusMap;
    dimensionMessage: string;
    shieldType: string;
    isAck: boolean;
    duration: string;
    id: number;
    title: string;
    eventId: string;
    latestAnomalyTime: string;
    isShielded: boolean;
    strategyName: string;
    firstAnomalyTime: string;
}

export type IStatusMap = {
    [p in EventStatus]: VueI18n.TranslateResult;
}

export type ValueOf<T> = T[keyof T];

export type EventStatus = 'ABNORMAL' | 'SHIELD_ABNORMAL' | 'CLOSED' | 'RECOVERED'

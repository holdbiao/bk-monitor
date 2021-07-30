<script>
    export default {
        name: 'bk-search-select-menu',
        props: {
            list: {
                type: Array,
                default () {
                    return []
                }
            },
            isCondition: Boolean,
            condition: Object,
            displayKey: {
                type: String,
                require: true
            },
            filter: {
                type: String,
                default: ''
            },
            error: {
                type: String,
                default: ''
            },
            multiable: Boolean,
            child: Boolean,
            loading: Boolean,
            remoteEmptyText: String,
            remoteLoadingText: String,
            checked: {
                type: Object,
                default () {
                    return {}
                }
            },
            primaryKey: {
                type: String,
                require: true
            }
        },
        methods: {
            handleClick (item, index, e, check, id) {
                if (check) {
                    this.$emit('select', item, index)
                } else {
                    this.$refs[id].style.display = this.checked[item[this.primaryKey]] ? 'none' : 'block'
                    this.$emit('select-check', item, index)
                }
            },
            handleCheckClick (item, index, next, old, id) {
                this.$emit('select-check', item, index, next, old)
            },
            setCheckValue (item, val) {
                const ref = this.$refs[item[this.primaryKey]]
                if (ref) {
                    ref.style.display = this.checked[item[this.primaryKey]] ? 'none' : 'block'
                }
            },
            handleSelectEnter (e) {
                this.$emit('select-enter', e)
            },
            handleKeyDown (e) {
                if ((e.code === 'Enter' || e.code === 'NumpadEnter')) {
                    this.handleSelectEnter(e)
                }
            }
        },
        render (h) {
            const {
                list,
                condition,
                displayKey,
                primaryKey,
                filter,
                multiable,
                child,
                checked,
                remoteLoadingText,
                remoteEmptyText,
                loading = false,
                isCondition = false,
                error = ''
            } = this
            if (error) {
                return (<div class={{ 'bk-search-list': true }}>
                <div class={{ 'bk-search-list-error': true }}>{error}</div>
            </div>)
            } else if (!loading && (!list || !list.length)) {
                return (<div class={{ 'bk-search-list': true }}>
                <div class={{ 'bk-search-list-loading': true }}>{remoteEmptyText}</div>
            </div>)
            }
            const conditionEvent = { on: {} }
            const wrapEvent = { on: {} }
            const footerEnterEvent = { on: {} }
            const items = this._l(list, (item, index) => {
                const id = item[primaryKey]
                const isFilter = filter && item[displayKey].includes(filter)
                const text = item[displayKey]
                let i, pre, next
                const events = {
                    on: {}
                }
                events.on.click = e => this.handleClick(item, index, e, !multiable || !child, id)
                if (isFilter) {
                    i = text.indexOf(filter)
                    pre = text.slice(0, i)
                    next = text.slice(i + filter.length, text.length)
                }
                return (
                <li class={{ 'bk-search-list-menu-item': true, 'is-group': !!item.isGroup }}>
                    <div {...events} class={{ 'item-name': true }}>
                        {isFilter
                            ? <div>{pre} <span class={{ 'item-name-filter': true }}>{filter}</span>{next}</div> : text}
                    </div>
                    <span v-show={multiable && child && checked[text]}
                        ref={id}
                        class={{ 'bk-icon icon-check-1 item-icon': true }}></span>
                </li>)
            })
            if (multiable && child) {
                wrapEvent['on']['keydown'] = e => this.handleKeyDown(e)
                footerEnterEvent['on']['click'] = e => this.handleSelectEnter(e)
            }
            if (isCondition) {
                conditionEvent['on']['click'] = _ => this.$emit('select-conditon', condition)
            }
            return (
            <div class={{ 'bk-search-list': true }} {...wrapEvent} tabIndex="-1">
                <div v-show={loading}>{remoteLoadingText}</div>
                <div v-show={!loading}>
                    {!isCondition
                        ? ''
                        : <div class={{ 'bk-search-list-condition': true }}{...conditionEvent}>
                            {condition[displayKey]}
                        </div>}
                    <ul class={{ 'bk-search-list-menu': true }}>
                        {items}
                    </ul>
                </div>
                {multiable && child
                    ? <div class={{ 'bk-search-list-footer': true }}>
                        <span class={{ 'footer-btn': true }} {...footerEnterEvent}>确认</span>
                        <span class={{ 'footer-btn': true }}>取消</span>
                    </div> : ''
                }
            </div>
        )
        }
    }
</script>

<style lang="scss">
    .bk-search-list {
        font-family: 微软雅黑 PingFang-SC;
        font-size: 12px;
        position: relative;
        max-height: 280px;
        min-height: 32px;
        min-width: 230px;
        line-height: 32px;
        color: #63656E;
        margin: -.3rem -.6rem;
        outline: none;
        resize: none;
        pointer-events: all;
        &-condition {
            border-bottom: 1px solid #DCDEE5;
            padding: 0 10px 0 16px;
            pointer-events: auto;
            &:hover {
                cursor: pointer;
                color: #3a84ff;
                background-color: rgba(234, 243, 255, .7);
            }
        }
        &-menu {
            margin: 0;
            padding: 6px 0;
            display: flex;
            flex-direction: column;
            pointer-events: all;
            max-height: 200px;
            overflow-x: hidden;
            overflow-y: auto;
            .is-group{
                border-bottom: 1px solid #DCDEE5;
            }
            &-item {
                flex: 1 0 32px;
                display: flex;
                align-items: center;
                justify-content: flex-start;
                pointer-events: auto;
                text-overflow: ellipsis;
                overflow: hidden;
                white-space: nowrap;
                padding: 0 10px 0 16px;
                .item-name {
                    flex: 1;
                    line-height: 32px;
                    &-filter {
                        color: #313238;
                    }
                }
                .item-icon {
                    color: #3a84ff;
                    font-size: 12px;
                    font-weight: bold;
                }
                &:hover {
                    cursor: pointer;
                    color: #3a84ff;
                    background-color: rgba(234, 243, 255, .7);
                }
            }
            &::-webkit-scrollbar {
                width: 3px;
                height: 5px;
            }
            &::-webkit-scrollbar-thumb {
                border-radius: 20px;
                background: #e6e9ea;
                box-shadow: inset 0 0 6px rgba(204, 204, 204, 0.3);
            }
        }
        &-loading {
            padding: 0 10px 0 16px;
            line-height: 32px;
        }
        &-error {
            padding: 0 10px 0 16px;
            line-height: 32px;
            font-weight: bold;
        }
        &-footer {
            display: flex;
            line-height: 32px;
            flex-direction: row;
            justify-content: space-around;
            align-items: center;
            margin: 0 -10px -6px -16px;
            pointer-events: auto;
            .footer-btn {
                flex: 1;
                text-align: center;
                border-top: 1px solid #DCDEE5;
                pointer-events: auto;
                &:hover {
                    cursor: pointer;
                    color: #3a84ff;
                    background-color: rgba(234, 243, 255, .7);
                }
                &:first-child {
                    border-right: 1px solid #DCDEE5;
                }
            }
        }
    }
</style>

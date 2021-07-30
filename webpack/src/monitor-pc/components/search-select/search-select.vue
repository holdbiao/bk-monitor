<template>
    <div ref="wrap"
        class="bk-search-select"
        :style="{ maxHeight: maxHeight + 'px' }"
        :class="{ 'is-focus': input.focus }">
        <div class="search-prefix">
            <slot name="prefix"></slot>
        </div>
        <div class="search-input">
            <div v-for="(item,index) in chip.list" class="search-input-chip" :key="index">
                <span class="chip-name">
                    {{item[displayKey] + (item.values && item.values.length ? explainCode + item.values.map(v => v[displayKey]).join(splitCode) : '')}}
                </span>
                <span class="chip-clear bk-icon icon-close" @click="handleClear(index,item)"></span>
            </div>
            <div class="search-input-input">
                <div
                    ref="input"
                    class="div-input"
                    :class="{ 'input-before': !input.value.length }"
                    contenteditable="plaintext-only"
                    :data-placeholder="placeholder"
                    @click="handleInputClick"
                    v-clickoutside="handleInputOutSide"
                    @focus="handleInputFocus"
                    @cut="handleInputCut"
                    @input="handleInputChange"
                    @keydown="handleInputKeyup">
                </div>
            </div>
        </div>
        <div class="search-nextfix">
            <i v-if="!$slots.nextfix" class="bk-icon icon-search search-nextfix-icon"
                :class="{ 'is-focus': input.focus }"></i>
            <slot v-else name="nextfix"></slot>
        </div>
    </div>
</template>

<script>
    import SearchInputMenu from './search-select-menu'
    import { debounce } from 'throttle-debounce'
    export default {
        name: 'bk-search-select',
        components: {
            // eslint-disable-next-line vue/no-unused-components
            SearchInputMenu
        },
        model: {
            prop: 'values',
            event: 'change'
        },
        props: {
            splitCode: {
                type: String,
                default: ' | '
            },
            explainCode: {
                type: String,
                default: '：'
            },
            placeholder: {
                type: String,
                default () {
                    return this.$t('请输入')
                }
            },
            emptyText: {
                type: String,
                default () {
                    return this.$t('包含键值得过滤查询必须有一个值')
                }
            },
            maxHeight: {
                type: [String, Number],
                default: 57
            },
            showDelay: {
                type: Number,
                default: 100
            },
            displayKey: {
                type: String,
                default: 'name'
            },
            primaryKey: {
                type: String,
                default: 'id'
            },
            condition: {
                type: Object,
                default () {
                    return {
                        name: this.$t('或')
                    }
                }
            },
            values: {
                type: Array,
                default () {
                    return []
                }
            },
            filter: Boolean,
            filterChildrenMethod: Function,
            filterMenuMethod: Function,
            remote: {
                type: Boolean,
                default: false
            },
            remoteMethod: Function,
            remoteEmptyText: {
                type: String,
                default () {
                    return this.$t('查询无数据')
                }
            },
            remoteLoadingText: {
                type: String,
                default () {
                    return this.$t('正在加载中...')
                }
            },
            multiable: {
                type: Boolean,
                default: true
            },
            keyDelay: {
                type: Number,
                default: 300
            }
        },
        data () {
            return {
                data: [
                    {
                        name: this.$t('测试一'),
                        id: '1',
                        children: [
                            {
                                name: '测试1-2',
                                id: '1-2'
                            },
                            {
                                name: '测试1-3',
                                id: '1-3'
                            },
                            {
                                name: '测试1-4',
                                id: '1-4'
                            }
                        ]
                    },
                    {
                        name: this.$t('测试二'),
                        id: '2',
                        children: [
                            {
                                name: '测试二-2',
                                id: '2-1'
                            },
                            {
                                name: '测试二-3',
                                id: '2-2'
                            },
                            {
                                name: '测试二-4',
                                id: '2-3'
                            },
                            {
                                name: this.$t('测试五'),
                                id: '2-5'
                            },
                            {
                                name: this.$t('测试六'),
                                id: '2-6'
                            },
                            {
                                name: this.$t('测试三'),
                                id: '2-33'
                            },
                            {
                                name: this.$t('测试四'),
                                id: '2-44'
                            },
                            {
                                name: this.$t('测试五'),
                                id: '2-55'
                            },
                            {
                                name: this.$t('测试六'),
                                id: '2-66'
                            }
                        ]
                    },
                    {
                        name: this.$t('测试三'),
                        id: '3'
                    },
                    {
                        name: this.$t('测试四'),
                        id: '4'
                    },
                    {
                        name: this.$t('测试五'),
                        id: '5'
                    },
                    {
                        name: this.$t('测试六'),
                        id: '6'
                    },
                    {
                        name: this.$t('测试三'),
                        id: '33'
                    },
                    {
                        name: this.$t('测试四'),
                        id: '44'
                    },
                    {
                        name: this.$t('测试五'),
                        id: '55'
                    },
                    {
                        name: this.$t('测试六'),
                        id: '66'
                    }
                ],
                menuInstance: null,
                popperMenuInstance: null,
                menuChildInstance: null,
                menu: {
                    active: -1,
                    child: false,
                    checked: {},
                    loading: false
                },
                chip: {
                    list: []
                },
                input: {
                    focus: false,
                    value: ''
                },
                handleInputSearchPlus () {

                }
            }
        },
        computed: {
            curItem () {
                return this.data[this.menu.active] || {}
            },
            childList () {
                const ret = []
                let i = 0
                while (i < this.data.length) {
                    const item = this.data[i]
                    if (item.children && item.children.length) {
                        ret.push(...item.children)
                    }
                    i++
                }
                return ret
            }
        },
        watch: {
            values: {
                handler (v) {
                    if (v !== this.chip.list) {
                        this.chip.list = [...v]
                    }
                },
                deep: true,
                immediate: true
            }
        },
        created () {
            if (!Object.keys(this.condition).includes(this.displayKey)) {
                this.condition[this.displayKey] = this.$t('或')
            }
            this.handleInputSearchPlus = debounce(this.keyDelay, (v) => this.handleSearch(v))
        },
        beforeDestroy () {
            this.menuInstance = null
            this.menuChildInstance = null
            this.popperMenuInstance && this.popperMenuInstance.destroy(true)
        },
        methods: {
            initMenu () {
                if (!this.menuInstance) {
                    this.menuInstance = new window.Vue(SearchInputMenu).$mount()
                    this.menuInstance.condition = this.condition
                    this.menuInstance.displayKey = this.displayKey
                    this.menuInstance.primaryKey = this.primaryKey
                    this.menuInstance.multiable = this.multiable
                    this.menuInstance.$on('select', this.handleMenuSelect)
                    this.menuInstance.$on('select-conditon', this.handleSelectConditon)
                }
            },
            initChildMenu () {
                this.menuChildInstance = new window.Vue(SearchInputMenu).$mount()
                this.menuChildInstance.displayKey = this.displayKey
                this.menuChildInstance.primaryKey = this.primaryKey
                this.menuChildInstance.multiable = this.multiable
                this.menuChildInstance.child = true
                this.menuChildInstance.remoteEmptyText = this.remoteEmptyText
                this.menuChildInstance.remoteLoadingText = this.remoteLoadingText
                this.menuChildInstance.$on('select', this.handleMenuChildSelect)
                this.menuChildInstance.$on('select-check', this.handleSelectCheck)
                this.menuChildInstance.$on('select-enter', this.handleKeyEnter)
            },
            initPopover (el) {
                if (!this.popperMenuInstance) {
                    this.popperMenuInstance = this.$bkPopover(this.$refs.input, {
                        content: el || this.menuInstance.$el,
                        arrow: false,
                        placement: 'bottom-start',
                        trigger: 'manual',
                        theme: 'light',
                        hideOnClick: false,
                        distance: -this.$refs.wrap.clientHeight,
                        lazy: false,
                        ignoreAttributes: true
                    }, true)
                    // this.popperMenuInstance = instance.instances[0]
                }
            },
            showMenu () {
                if (!this.menuInstance) {
                    this.initMenu()
                }
                this.menuInstance.isCondition = !!this.chip.list.length && this.chip.list[this.chip.list.length - 1][this.primaryKey] !== this.condition[this.primaryKey]
                this.menuInstance.list = this.data
                this.showPopper(this.menuInstance.$el)
                this.$emit('show-menu', this.menuInstance)
            },
            showChildMenu (list, filter) {
                this.menuChildInstance.filter = filter
                this.menuChildInstance.list = list
                this.showPopper(this.menuChildInstance.$el)
            },
            showPopper (el) {
                if (!this.popperMenuInstance) {
                    this.initPopover()
                } else {
                    this.popperMenuInstance.set({
                        distance: -this.$refs.wrap.clientHeight
                    })
                    this.popperMenuInstance.setContent(el)
                }
                this.popperMenuInstance.popperInstance.update()
                this.popperMenuInstance.show(this.showDelay)
            },
            hidePopper () {
                this.popperMenuInstance && this.popperMenuInstance.hide(0)
            },
            handleInputChange (e) {
                this.clearInput()
                let text = e.target.textContent
                if (/(\r|\n)/gm.test(text) || /\s{2}/gm.test(text)) {
                    e.preventDefault()
                    text = text.replace(/(\r|\n)/gm, this.splitCode).replace(/\s{2}/gm, '')
                    this.$refs.input.textContent = text
                    this.handleInputFocus()
                }
                this.input.value = text
                this.handleInputSearchPlus(text)
                this.$emit('input-change', e)
            },
            async handleSearch (text) {
                const include = this.input.value.includes(this.explainCode)
                let list = []
                if (include && this.menuChildInstance) {
                    const filter = text.replace(this.curItem[this.displayKey] + this.explainCode, '')
                    if (this.remote && typeof this.remoteMethod === 'function') {
                        this.menuChildInstance.loading = true
                        list = await this.remoteMethod(filter, this.curItem, this.menu.active).finally(() => {
                            this.menuChildInstance.loading = false
                        })
                        this.showChildMenu(list, filter)
                    } else {
                        list = this.handleFilter(filter)
                        if (list && list.length) {
                            this.showChildMenu(list, filter)
                        }
                    }
                } else if (!include && this.menuInstance) {
                    list = this.handleFilter(text)
                    if (list && list.length) {
                        this.menuInstance.filter = text
                        this.menuInstance.list = list
                        this.showPopper(this.menuInstance.$el)
                    }
                }
            },
            handleFilter (v) {
                let filterList = []
                if (!this.input.value.length || !~this.input.value.indexOf(this.explainCode)) {
                    if (this.filter && typeof this.filterMenuMethod === 'function') {
                        filterList = this.filterMenuMethod(this.data, v)
                    } else {
                        if (v.length) {
                            filterList = this.childList.filter(item => ~item[this.displayKey].indexOf(v))
                            if (filterList.length) {
                                let item = filterList[filterList.length - 1]
                                item = { ...item, isGroup: true }
                                filterList[filterList.length - 1] = item
                            }
                            filterList.push(...this.data.filter(item => ~item[this.displayKey].indexOf(v)))
                        } else {
                            filterList = this.data
                        }
                    }
                } else if (this.curItem.children && this.curItem.children.length) {
                    if (this.filter && typeof this.filterChildrenMethod === 'function') {
                        filterList = this.filterChildrenMethod(this.curItem.children, v)
                    } else {
                        filterList = this.curItem.children.filter(item => ~item[this.displayKey].indexOf(v))
                    }
                }
                return filterList
            },
            handleInputCut (e) {
                const selection = document.getSelection()
                if (selection.anchorOffset >= this.input.value.length) {
                    this.input.value = ''
                }
                this.$emit('input-cut', e)
            },
            handleInputOutSide (e) {
                const parent = e.target.offsetParent
                const classList = parent ? parent.classList : null
                if (classList && !(classList.contains('bk-search-list') || classList.contains('tippy-tooltip') || classList.contains('bk-form-checkbox') || classList.contains('search-input-list'))) {
                    this.hidePopper()
                    this.input.focus = false
                }
                this.$emit('input-click-outside', e)
            },
            handleInputClick (e) {
                this.input.focus = true
                if (!this.input.value) {
                    if (!this.menuInstance) {
                        this.initMenu()
                    }
                    this.menuInstance.isCondition = !!this.chip.list.length && this.chip.list[this.chip.list.length - 1][this.primaryKey] !== this.condition[this.primaryKey]
                    this.menuInstance.list = this.data
                    this.menu.child = false
                    this.$nextTick(_ => {
                        this.showPopper(this.menuInstance.$el)
                    })
                } else {
                    const cur = this.data[this.menu.active]
                    if (cur && cur.children && cur.children.length && this.popperMenuInstance) {
                        this.menu.child = true
                        this.popperMenuInstance.show(this.showDelay)
                    }
                }
                this.$emit('input-click', e)
            },
            handleInputFocus (e) {
                this.input.focus = true
                const input = this.$refs.input
                let selection = null
                if (window.getSelection) {
                    selection = window.getSelection()
                    selection.selectAllChildren(input)
                    selection.collapseToEnd()
                } else {
                    selection = document.onselectionchange.createRange()
                    selection.moveToElementText(input)
                    selection.collapse(false)
                    selection.select()
                }
                this.$emit('input-focus', e)
            },
            async updateChildMenu (item, index) {
                const isChild = item.children && item.children.length
                const isRemote = this.remote && typeof this.remoteMethod === 'function'
                if (isChild || isRemote) {
                    if (!this.menuChildInstance || this.multiable) {
                        this.initChildMenu()
                    }
                    this.menuChildInstance.error = ''
                    this.menuChildInstance.loading = isRemote
                    this.menuChildInstance.checked = this.menu.checked
                    this.showPopper(this.menuChildInstance.$el)
                    this.menu.child = true
                    if (isRemote) {
                        const list = await this.remoteMethod(this.input.value, item, index).finally(() => {
                            this.menuChildInstance.loading = false
                        })
                        this.menuChildInstance.list = list
                    } else {
                        this.menuChildInstance.list = item.children
                    }
                } else {
                    this.hidePopper()
                    this.handleInputFocus()
                }
            },
            handleMenuSelect (item, index) {
                const isChildClick = ~this.data.findIndex(set => set[this.primaryKey] === item[this.primaryKey])
                if (!isChildClick) {
                    this.input.value = item[this.displayKey]
                    this.$nextTick().then(() => {
                        this.updateInput(this.input.value)
                        this.handleKeyEnter()
                    })
                } else {
                    this.menu.active = index
                    this.input.value = item[this.displayKey] + this.explainCode
                    this.$nextTick().then(() => {
                        this.updateInput(this.input.value)
                        this.updateChildMenu(item, index)
                        this.$emit('menu-select', item, index)
                    })
                }
            },
            handleMenuChildSelect (item, index) {
                this.input.value += item[this.displayKey]
                this.updateInput(this.input.value)
                this.handleEnter(this.input.value, item, true)
                this.$emit('menu-child-select', item, index)
            },
            handleInputKeyup (e) {
                switch (e.code) {
                    case 'Enter':
                    case 'NumpadEnter':
                        this.handleKeyEnter(e)
                        break
                    case 'Backspace':
                        this.handleKeyBackspace(e)
                        break
                    default:
                        this.handleKeyDefault(e)
                        break
                }
            },
            handleKeyDefault (e) {
                if (Object.keys(this.menu.checked).length) {
                    e.preventDefault()
                    return false
                }
            },
            handleKeyBackspace (e) {
                const keys = Object.keys(this.menu.checked)
                if (this.multiable && keys.length) {
                    const key = keys[keys.length - 1]
                    this.menuChildInstance && this.menuChildInstance.setCheckValue(this.menu.checked[key], false)
                    delete this.menu.checked[key]
                    this.updateCheckedInputVal()
                    e.preventDefault()
                    return false
                }
                if (!this.input.value && !(!this.chip.list.length && !this.$refs.input.textContent.length)) {
                    const item = this.chip.list.pop()
                    this.$nextTick().then(() => {
                        this.showMenu()
                    })
                    this.$emit('change', this.chip.list)
                    this.$emit('key-delete', item)
                } else {
                    if (!this.input.value.includes(this.curItem[this.displayKey] + this.explainCode)) {
                        this.menu.active = -1
                    }
                }
            },
            handleKeyEnter (e) {
                if (!this.input.value) return
                if (this.input.value === this.curItem[this.displayKey] + this.explainCode) {
                    e.preventDefault()
                    this.menuChildInstance.error = this.emptyText
                    this.$nextTick(_ => {
                        this.showPopper(this.menuChildInstance.$el)
                    })
                    this.handleInputFocus()
                } else {
                    if (this.menu.active >= 0) {
                        const val = this.input.value.replace(this.curItem[this.displayKey] + this.explainCode, '')
                        this.handleEnter(this.input.value, { [this.primaryKey]: val, [this.displayKey]: val }, true)
                    } else {
                        this.handleEnter(this.input.value, {
                            [this.primaryKey]: this.input.value,
                            [this.displayKey]: this.input.value
                        })
                    }
                }
                this.$emit('key-enter')
            },
            handleEnter (val, item, child = false) {
                if (child) {
                    if (this.input.value === this.condition[this.displayKey]) {
                        this.chip.list.push(this.condition)
                    } else {
                        let values = []
                        if (Object.keys(this.menu.checked).length) {
                            values = Object.values(this.menu.checked)
                        } else {
                            values.push(item)
                        }
                        const data = Object.assign({}, this.curItem, { values })
                        if (data.children && data.children.length) {
                            delete data.children
                        }
                        this.chip.list.push(data)
                    }
                } else {
                    this.chip.list.push(item)
                }
                this.menu.checked = {}
                this.menu.active = -1
                this.input.value = ''
                this.updateInput()
                this.menuInstance.filter = ''
                this.showMenu()
                this.$refs.input.focus()
                this.$emit('change', this.chip.list)
            },
            handleClear (index, item) {
                const name = this.chip.list.splice(index, 1)
                !this.input.value.length && this.showMenu()
                this.$emit('change', this.chip.list)
                this.$emit('chip-del', name)
            },
            handleSelectConditon (item) {
                this.input.value = item[this.displayKey]
                this.updateInput(this.input.value)
                this.handleEnter(this.input.value, item, true)
                this.$emit('condition-select', item)
            },
            handleSelectCheck (item, index) {
                const next = !this.menu.checked[item[this.primaryKey]]
                if (next) {
                    this.menu.checked[item[this.primaryKey]] = item
                } else {
                    delete this.menu.checked[item[this.primaryKey]]
                }
                this.menuChildInstance.checked = this.menu.checked
                this.updateCheckedInputVal()
                this.$emit('child-checked', item, index, next)
            },
            updateCheckedInputVal () {
                if (this.menu.active >= 0) {
                    const val = Object.values(this.menu.checked).map(set => set[this.displayKey]).join(this.splitCode)
                    this.input.value = this.curItem[this.displayKey] + this.explainCode + val
                    this.updateInput(this.input.value)
                }
            },
            updateInput (val = '') {
                this.$refs.input.innerText = val
            },
            clearInput () {
                const text = this.$refs.input.innerText
                if (text[text.length - 1] === '\n' || text[0] === '\r') {
                    this.updateInput(text.slice(0, -1))
                    this.clearInput()
                } else if (text[0] === '\n' || text[0] === '\r') {
                    this.updateInput(text.slice(1))
                    this.clearInput()
                }
            },
            getMenuInstance () {
                return this.menuInstance
            },
            getChildMenuInstance () {
                return this.menuChildInstance
            },
            getInputInstance () {
                return this.$refs.input
            }
        }
    }
</script>

<style scoped lang="scss">
    .bk-search-select {
        display: flex;
        flex-direction: row;
        align-items: center;
        font-size: 12px;
        min-height: 30px;
        box-sizing: border-box;
        position: relative;
        border: 1px solid #c4c6cc;
        border-radius: 2px;
        outline: none;
        resize: none;
        transition: border .2s linear;
        overflow: auto;
        color: #63656e;
        flex-wrap: wrap;
        .search-prefix {
            flex: 0 0 auto;
            display: flex;
            align-items: center;
            height: 100%;
        }
        .search-input {
            flex: 1;
            position: relative;
            padding: 0 2px;
            text-align: left;
            overflow: visible;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            height: 100%;
            &-chip {
                flex: 0 0 auto;
                max-width: 99%;
                display: inline-block;
                align-self: center;
                color: #63656E;
                margin: 0 0 0 6px;
                padding-left: 8px;
                position: relative;
                background: #F0F1F5;
                border: 1px solid #DCDEE5;
                border-radius: 2px;
                line-height: 20px;
                &:hover {
                    background: #DCDEE5;
                    .chip-clear {
                        color: #63656E;
                    }
                }
                .chip-name {
                    display: inline-block;
                    margin-right: 20px;
                    word-break: break-all;
                }
                .chip-clear {
                    color: #979BA5;
                    position: absolute;
                    right: 3px;
                    line-height: normal;
                    display: inline-block;
                    top: 4px;
                    text-align: center;
                    cursor: pointer;
                }
            }
            &-input {
                position: relative;
                padding: 0 10px;
                color: #63656e;
                flex: 1 1 auto;
                border: none;
                height: 100%;
                min-width: 40px;
                display: flex;
                align-items: center;
                .div-input {
                    flex: 1 1 auto;
                    line-height: 20px;
                    padding: 6px 0;
                    height: 100%;
                    word-break: break-all;
                }
                .input-before {
                    &:before {
                        content: attr(data-placeholder);
                        color: #C4C6CC;
                        padding-left: 2px;
                    }
                }
            }
        }
        .search-nextfix {
            @extend .search-prefix;
            color: #c4c6cc;
            &-icon {
                margin-right: 8px;
                font-size: 16px;
                transition: color .2s linear;
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
        @at-root {
            .is-focus {
                border-color: #3c96ff !important;
                background: #fff !important;
                color: #3c96ff;
            }
        }
    }
</style>

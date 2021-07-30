<template>
    <div class="static-input">
        <bk-input
            class="static-input-text" :placeholder="$t('多个IP以回车为分隔符')"
            v-model="text"
            @keydown.native="handleInputKeydown"
            @change="handleSearch"
            :type="'textarea'"
            :rows="10">
        </bk-input>
        <slot></slot>
        <div class="static-input-btn" @click="handleChecked"> {{ $t('添加至列表') }} </div>
    </div>
</template>
<script>
    import { debounce } from 'throttle-debounce'
    export default {
        name: 'static-input',
        props: {
            defaultText: String,
            type: String
        },
        data () {
            return {
                ipMatch: /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])(\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])){3}$/,
                text: '',
                handleSearch () {

                }
            }
        },
        watch: {
            defaultText: {
                handler (v) {
                    this.text = (v + '').trim().replace(/(\r|\n){2,}/gm, '\n')
                },
                immediate: true
            }
        },
        created () {
            this.handleSearch = debounce(300, this.handleKeywordChange)
        },
        methods: {
            handleIpChange (v) {
                // this.$emit('change', v)
            },
            handleInputKeydown (e) {
                if (e.key === 'enter') {
                    return true
                }
                if (e.ctrlKey || e.shilftKey || e.metaKey) {
                    return true
                }
                if (!e.key.match(/[0-9\.\s\|\,\;]/) && !e.key.match(/(backspace|enter|ctrl|shift|tab)/mi)) {
                    e.preventDefault()
                }
            },
            handleChecked () {
                if (this.text && this.text.length) {
                    const ipList = this.text.split(/[\r\n]+/gm)
                    const errList = new Set()
                    const goodList = new Set()
                    ipList.forEach(ip => {
                        ip = ip.trim()
                        if (ip.match(this.ipMatch)) {
                            goodList.add(ip)
                        } else {
                            ip.length > 0 && errList.add(ip)
                        }
                    })
                    if (errList.size > 0) {
                        this.text = Array.from(errList).join('\n')
                    }
                    if (goodList.size > 0 || errList.size > 0) {
                        // this.$emit('checked', 'static-ip', Array.from(goodList).join('\n'), this.text)
                        this.$emit('checked', this.type, { goodList: Array.from(goodList), errList: Array.from(errList) }, this.text)
                    }
                }
            },
            handleKeywordChange (v) {
                this.$emit('change-input', v)
            }
        }
    }
</script>
<style lang="scss" scoped>
    .static-input {
        &-text {
            margin: 10px 0;
        }
        &-btn {
            min-width: 200px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #3A84FF;
            border-radius: 2px;
            color: #3A84FF;
            cursor: pointer;
            &:hover {
                background: #3A84FF;
                color: #FFFFFF;
            }
        }
    }
</style>

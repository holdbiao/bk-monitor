<template>
    <div :style="{ height: calcSize(height),width: width }"></div>
</template>

<script>
    export default {
        name: 'ace-editor',
        props: {
            value: {
                type: String,
                default: ''
            },
            width: {
                type: [Number, String],
                default: '100%'
            },
            height: {
                type: [Number, String],
                default: 320
            },
            lang: {
                type: String,
                default: 'javascript'
            },
            theme: {
                type: String,
                default: 'monokai'
            },
            readOnly: {
                type: Boolean,
                default: false
            },
            fullScreen: {
                type: Boolean,
                default: false
            },
            hasError: {
                type: Boolean,
                default: false
            }
        },
        data () {
            return {
                $ace: null
            }
        },
        watch: {
            fullScreen () {
                this.$el.classList.toggle('ace-full-screen')
                this.$ace.resize()
            }
        },
        mounted () {
            const ace = window.ace
            this.$ace = ace.edit(this.$el)
            const {
                $ace,
                lang,
                theme,
                readOnly
            } = this
            $ace.$blockScrolling = Infinity
            $ace.getSession().setMode('ace/mode/' + lang)
            $ace.getSession().setNewLineMode('unix')
            $ace.setTheme('ace/theme/' + theme)
            $ace.setOptions({
                enableBasicAutocompletion: true,
                enableSnippets: true,
                enableLiveAutocompletion: true,
                fontSize: '12pt'
            })
            $ace.setReadOnly(readOnly) // 设置是否为只读模式
            $ace.setShowPrintMargin(false) // 不显示打印边距
            $ace.setValue(this.value, 1)
            // 绑定输入事件回调
            $ace.on('change', ($editor, $fn) => {
                this.$emit('input', $ace.getValue(), $editor, $fn)
            })

        // $ace.on('blur', ($editor, $fn) => {
        //     var content = $ace.getValue()
        //     // this.$emit('update:hasError', !content)
        //     this.$emit('blur', content, $editor, $fn)
        // })

        // session.on('changeAnnotation', (args, instance) => {
        //     const annotations = instance.$annotations
        //     if (annotations && annotations.length) {
        //         this.$emit('change-annotation', annotations)
        //     }
        // })
        },
        methods: {
            calcSize (size) {
                const _size = size.toString()

                if (_size.match(/^\d*$/)) return `${size}px`
                if (_size.match(/^[0-9]?%$/)) return _size

                return '100%'
            }
        }
    }
</script>

<style scoped>

</style>

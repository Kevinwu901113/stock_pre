// 表单相关类型定义

// 基础表单字段类型
export type FormFieldType = 
  | 'text'
  | 'password'
  | 'email'
  | 'number'
  | 'tel'
  | 'url'
  | 'textarea'
  | 'select'
  | 'multiselect'
  | 'radio'
  | 'checkbox'
  | 'switch'
  | 'date'
  | 'datetime'
  | 'time'
  | 'daterange'
  | 'file'
  | 'slider'
  | 'rate'
  | 'color'
  | 'hidden'
  | 'custom'

// 表单字段选项
export interface FormFieldOption {
  label: string
  value: any
  disabled?: boolean
  color?: string
  icon?: string
  description?: string
}

// 表单验证规则
export interface FormValidationRule {
  required?: boolean
  message?: string
  min?: number
  max?: number
  pattern?: RegExp | string
  validator?: (value: any, formData: any) => boolean | string | Promise<boolean | string>
  trigger?: 'change' | 'blur' | 'submit'
}

// 表单字段定义
export interface FormField {
  name: string
  label: string
  type: FormFieldType
  placeholder?: string
  defaultValue?: any
  value?: any
  options?: FormFieldOption[]
  rules?: FormValidationRule[]
  disabled?: boolean
  readonly?: boolean
  hidden?: boolean
  required?: boolean
  span?: number
  offset?: number
  tooltip?: string
  help?: string
  prefix?: string
  suffix?: string
  addonBefore?: string
  addonAfter?: string
  size?: 'small' | 'middle' | 'large'
  allowClear?: boolean
  showCount?: boolean
  maxLength?: number
  rows?: number
  autoSize?: boolean | { minRows?: number; maxRows?: number }
  multiple?: boolean
  searchable?: boolean
  loading?: boolean
  showSearch?: boolean
  filterOption?: boolean | ((input: string, option: FormFieldOption) => boolean)
  mode?: 'multiple' | 'tags'
  showTime?: boolean
  format?: string
  disabledDate?: (current: Date) => boolean
  disabledTime?: (current: Date) => any
  accept?: string
  maxSize?: number
  maxCount?: number
  listType?: 'text' | 'picture' | 'picture-card'
  beforeUpload?: (file: File) => boolean | Promise<boolean>
  customRequest?: (options: any) => void
  min?: number
  max?: number
  step?: number
  precision?: number
  marks?: Record<number, string>
  range?: boolean
  vertical?: boolean
  included?: boolean
  count?: number
  allowHalf?: boolean
  character?: string
  showAlpha?: boolean
  showText?: boolean
  presets?: { label: string; colors: string[] }[]
  dependencies?: string[]
  conditional?: {
    field: string
    value: any
    operator?: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'nin'
  }
  render?: (value: any, formData: any, field: FormField) => React.ReactNode
  onChange?: (value: any, formData: any) => void
  onBlur?: (value: any, formData: any) => void
  onFocus?: (value: any, formData: any) => void
}

// 表单布局类型
export type FormLayout = 'horizontal' | 'vertical' | 'inline'

// 表单尺寸类型
export type FormSize = 'small' | 'middle' | 'large'

// 表单配置
export interface FormConfig {
  layout?: FormLayout
  size?: FormSize
  labelCol?: {
    span?: number
    offset?: number
    xs?: number
    sm?: number
    md?: number
    lg?: number
    xl?: number
    xxl?: number
  }
  wrapperCol?: {
    span?: number
    offset?: number
    xs?: number
    sm?: number
    md?: number
    lg?: number
    xl?: number
    xxl?: number
  }
  colon?: boolean
  disabled?: boolean
  requiredMark?: boolean | 'optional'
  scrollToFirstError?: boolean
  validateTrigger?: 'onChange' | 'onBlur' | 'onSubmit'
  preserve?: boolean
  autoComplete?: 'on' | 'off'
}

// 表单数据类型
export interface FormData {
  [key: string]: any
}

// 表单错误类型
export interface FormError {
  field: string
  message: string
  rule?: string
}

// 表单状态类型
export interface FormState {
  data: FormData
  errors: FormError[]
  touched: Record<string, boolean>
  dirty: Record<string, boolean>
  submitting: boolean
  validating: boolean
  valid: boolean
}

// 表单操作类型
export interface FormActions {
  setFieldValue: (field: string, value: any) => void
  setFieldError: (field: string, error: string) => void
  setFieldTouched: (field: string, touched: boolean) => void
  setValues: (values: FormData) => void
  setErrors: (errors: FormError[]) => void
  clearErrors: () => void
  clearField: (field: string) => void
  resetForm: () => void
  validateField: (field: string) => Promise<boolean>
  validateForm: () => Promise<boolean>
  submitForm: () => Promise<void>
}

// 表单钩子返回类型
export interface FormHookReturn {
  formState: FormState
  formActions: FormActions
  register: (field: FormField) => {
    name: string
    value: any
    onChange: (value: any) => void
    onBlur: () => void
    error?: string
  }
}

// 动态表单配置
export interface DynamicFormConfig extends FormConfig {
  fields: FormField[]
  sections?: FormSection[]
  initialValues?: FormData
  validationSchema?: any
  onSubmit?: (values: FormData) => void | Promise<void>
  onValuesChange?: (changedValues: FormData, allValues: FormData) => void
  onFieldsChange?: (changedFields: any[], allFields: any[]) => void
}

// 表单分组
export interface FormSection {
  title?: string
  description?: string
  fields: string[]
  collapsible?: boolean
  defaultCollapsed?: boolean
  span?: number
  className?: string
}

// 表单步骤
export interface FormStep {
  title: string
  description?: string
  icon?: string
  fields: string[]
  optional?: boolean
  disabled?: boolean
  status?: 'wait' | 'process' | 'finish' | 'error'
}

// 分步表单配置
export interface StepFormConfig extends FormConfig {
  steps: FormStep[]
  current?: number
  direction?: 'horizontal' | 'vertical'
  size?: 'default' | 'small'
  status?: 'wait' | 'process' | 'finish' | 'error'
  onChange?: (current: number) => void
  onStepClick?: (current: number) => void
}

// 表单模板类型
export interface FormTemplate {
  id: string
  name: string
  description?: string
  category?: string
  config: DynamicFormConfig
  preview?: string
  tags?: string[]
  created_at: string
  updated_at: string
}

// 表单主题配置
export interface FormTheme {
  primaryColor?: string
  borderRadius?: number
  fontSize?: number
  spacing?: number
  labelColor?: string
  inputBackgroundColor?: string
  inputBorderColor?: string
  errorColor?: string
  successColor?: string
  warningColor?: string
}

// 表单国际化
export interface FormI18n {
  required: string
  invalid: string
  tooShort: string
  tooLong: string
  tooSmall: string
  tooLarge: string
  invalidEmail: string
  invalidUrl: string
  invalidDate: string
  invalidNumber: string
  invalidPattern: string
  submit: string
  reset: string
  cancel: string
  next: string
  previous: string
  finish: string
  loading: string
  uploading: string
  uploadSuccess: string
  uploadError: string
  selectFile: string
  dragToUpload: string
  searchPlaceholder: string
  noData: string
  selectAll: string
  deselectAll: string
}

// 表单导出配置
export interface FormExportConfig {
  format: 'json' | 'yaml' | 'xml'
  includeValues?: boolean
  includeValidation?: boolean
  includeLayout?: boolean
  minify?: boolean
}

// 表单导入配置
export interface FormImportConfig {
  format: 'json' | 'yaml' | 'xml'
  validateSchema?: boolean
  mergeMode?: 'replace' | 'merge' | 'append'
  skipInvalidFields?: boolean
}

// 表单事件类型
export interface FormEvent {
  type: 'change' | 'blur' | 'focus' | 'submit' | 'reset' | 'validate'
  field?: string
  value?: any
  error?: string
  timestamp: number
}

// 表单监听器类型
export type FormEventListener = (event: FormEvent) => void

// 表单插件接口
export interface FormPlugin {
  name: string
  version: string
  install: (formInstance: any) => void
  uninstall?: (formInstance: any) => void
}

// 表单实例类型
export interface FormInstance {
  getFieldValue: (field: string) => any
  getFieldsValue: (fields?: string[]) => FormData
  setFieldValue: (field: string, value: any) => void
  setFieldsValue: (values: FormData) => void
  validateFields: (fields?: string[]) => Promise<FormData>
  resetFields: (fields?: string[]) => void
  submit: () => Promise<void>
  getFieldError: (field: string) => string[]
  getFieldsError: (fields?: string[]) => any[]
  isFieldTouched: (field: string) => boolean
  isFieldsTouched: (fields?: string[]) => boolean
  isFieldValidating: (field: string) => boolean
  scrollToField: (field: string, options?: any) => void
}
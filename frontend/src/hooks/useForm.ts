// 表单相关的React Hooks

import { useState, useCallback, useRef, useEffect } from 'react'
import type {
  FormData,
  FormError,
  FormState,
  FormActions,
  FormHookReturn,
  FormValidationRule,
  FormField,
} from '@types/form'

// 表单验证函数类型
type ValidatorFunction = (value: any, formData: FormData) => string | null

// 内置验证器
const validators = {
  required: (message = '此字段为必填项'): ValidatorFunction => 
    (value) => {
      if (value === null || value === undefined || value === '' || 
          (Array.isArray(value) && value.length === 0)) {
        return message
      }
      return null
    },

  minLength: (min: number, message?: string): ValidatorFunction => 
    (value) => {
      if (typeof value === 'string' && value.length < min) {
        return message || `最少需要${min}个字符`
      }
      return null
    },

  maxLength: (max: number, message?: string): ValidatorFunction => 
    (value) => {
      if (typeof value === 'string' && value.length > max) {
        return message || `最多允许${max}个字符`
      }
      return null
    },

  pattern: (regex: RegExp, message = '格式不正确'): ValidatorFunction => 
    (value) => {
      if (typeof value === 'string' && !regex.test(value)) {
        return message
      }
      return null
    },

  email: (message = '请输入有效的邮箱地址'): ValidatorFunction => 
    validators.pattern(/^[^\s@]+@[^\s@]+\.[^\s@]+$/, message),

  phone: (message = '请输入有效的手机号码'): ValidatorFunction => 
    validators.pattern(/^1[3-9]\d{9}$/, message),

  number: (message = '请输入有效的数字'): ValidatorFunction => 
    (value) => {
      if (value !== '' && isNaN(Number(value))) {
        return message
      }
      return null
    },

  min: (min: number, message?: string): ValidatorFunction => 
    (value) => {
      const num = Number(value)
      if (!isNaN(num) && num < min) {
        return message || `值不能小于${min}`
      }
      return null
    },

  max: (max: number, message?: string): ValidatorFunction => 
    (value) => {
      const num = Number(value)
      if (!isNaN(num) && num > max) {
        return message || `值不能大于${max}`
      }
      return null
    },

  custom: (validator: (value: any, formData: FormData) => string | null): ValidatorFunction => 
    validator,
}

// 基础表单Hook
export function useForm<T extends FormData = FormData>(
  initialData: T = {} as T,
  options: {
    validateOnChange?: boolean
    validateOnBlur?: boolean
    resetOnSubmit?: boolean
    onSubmit?: (data: T) => Promise<void> | void
    onValidate?: (data: T) => FormError
  } = {}
): FormHookReturn<T> {
  const {
    validateOnChange = false,
    validateOnBlur = true,
    resetOnSubmit = false,
    onSubmit,
    onValidate,
  } = options

  const [state, setState] = useState<FormState<T>>({
    data: initialData,
    errors: {},
    touched: {},
    isDirty: false,
    isSubmitting: false,
    isValidating: false,
    isValid: true,
  })

  const validationRulesRef = useRef<Record<string, FormValidationRule[]>>({})
  const initialDataRef = useRef(initialData)

  // 设置字段值
  const setFieldValue = useCallback((name: string, value: any) => {
    setState(prev => {
      const newData = { ...prev.data, [name]: value }
      const isDirty = JSON.stringify(newData) !== JSON.stringify(initialDataRef.current)
      
      return {
        ...prev,
        data: newData,
        isDirty,
        errors: validateOnChange ? validateField(name, value, newData) : prev.errors,
      }
    })
  }, [validateOnChange])

  // 设置字段错误
  const setFieldError = useCallback((name: string, error: string | null) => {
    setState(prev => ({
      ...prev,
      errors: {
        ...prev.errors,
        [name]: error,
      },
    }))
  }, [])

  // 设置字段触碰状态
  const setFieldTouched = useCallback((name: string, touched = true) => {
    setState(prev => {
      const newTouched = { ...prev.touched, [name]: touched }
      let newErrors = prev.errors
      
      if (touched && validateOnBlur) {
        const fieldError = validateField(name, prev.data[name], prev.data)
        newErrors = { ...prev.errors, ...fieldError }
      }
      
      return {
        ...prev,
        touched: newTouched,
        errors: newErrors,
      }
    })
  }, [validateOnBlur])

  // 设置所有值
  const setValues = useCallback((data: Partial<T>) => {
    setState(prev => {
      const newData = { ...prev.data, ...data }
      const isDirty = JSON.stringify(newData) !== JSON.stringify(initialDataRef.current)
      
      return {
        ...prev,
        data: newData,
        isDirty,
      }
    })
  }, [])

  // 设置所有错误
  const setErrors = useCallback((errors: FormError) => {
    setState(prev => ({ ...prev, errors }))
  }, [])

  // 清除错误
  const clearErrors = useCallback((fieldNames?: string[]) => {
    setState(prev => {
      if (!fieldNames) {
        return { ...prev, errors: {} }
      }
      
      const newErrors = { ...prev.errors }
      fieldNames.forEach(name => {
        delete newErrors[name]
      })
      
      return { ...prev, errors: newErrors }
    })
  }, [])

  // 清除字段
  const clearField = useCallback((name: string) => {
    setState(prev => {
      const newData = { ...prev.data }
      delete newData[name]
      
      const newErrors = { ...prev.errors }
      delete newErrors[name]
      
      const newTouched = { ...prev.touched }
      delete newTouched[name]
      
      return {
        ...prev,
        data: newData,
        errors: newErrors,
        touched: newTouched,
      }
    })
  }, [])

  // 重置表单
  const reset = useCallback((newData?: T) => {
    const resetData = newData || initialDataRef.current
    setState({
      data: resetData,
      errors: {},
      touched: {},
      isDirty: false,
      isSubmitting: false,
      isValidating: false,
      isValid: true,
    })
    if (newData) {
      initialDataRef.current = newData
    }
  }, [])

  // 验证单个字段
  const validateField = useCallback((name: string, value: any, formData: T): FormError => {
    const rules = validationRulesRef.current[name] || []
    
    for (const rule of rules) {
      let validator: ValidatorFunction
      
      if (typeof rule === 'function') {
        validator = rule
      } else if (typeof rule === 'object' && rule.validator) {
        validator = rule.validator
      } else {
        continue
      }
      
      const error = validator(value, formData)
      if (error) {
        return { [name]: error }
      }
    }
    
    return {}
  }, [])

  // 验证整个表单
  const validate = useCallback(async (): Promise<boolean> => {
    setState(prev => ({ ...prev, isValidating: true }))
    
    try {
      let errors: FormError = {}
      
      // 验证所有字段
      Object.keys(validationRulesRef.current).forEach(name => {
        const fieldErrors = validateField(name, state.data[name], state.data)
        errors = { ...errors, ...fieldErrors }
      })
      
      // 自定义验证
      if (onValidate) {
        const customErrors = onValidate(state.data)
        errors = { ...errors, ...customErrors }
      }
      
      const isValid = Object.keys(errors).length === 0
      
      setState(prev => ({
        ...prev,
        errors,
        isValid,
        isValidating: false,
      }))
      
      return isValid
    } catch (error) {
      setState(prev => ({ ...prev, isValidating: false }))
      return false
    }
  }, [state.data, onValidate, validateField])

  // 提交表单
  const submit = useCallback(async () => {
    setState(prev => ({ ...prev, isSubmitting: true }))
    
    try {
      const isValid = await validate()
      
      if (isValid && onSubmit) {
        await onSubmit(state.data)
        
        if (resetOnSubmit) {
          reset()
        }
      }
    } catch (error) {
      console.error('Form submission error:', error)
    } finally {
      setState(prev => ({ ...prev, isSubmitting: false }))
    }
  }, [validate, onSubmit, state.data, resetOnSubmit, reset])

  // 注册字段
  const register = useCallback((name: string, rules: FormValidationRule[] = []) => {
    validationRulesRef.current[name] = rules
    
    return {
      name,
      value: state.data[name] || '',
      onChange: (value: any) => setFieldValue(name, value),
      onBlur: () => setFieldTouched(name),
      error: state.errors[name],
      touched: state.touched[name],
    }
  }, [state.data, state.errors, state.touched, setFieldValue, setFieldTouched])

  const actions: FormActions<T> = {
    setFieldValue,
    setFieldError,
    setFieldTouched,
    setValues,
    setErrors,
    clearErrors,
    clearField,
    reset,
    validate,
    submit,
  }

  return {
    ...state,
    ...actions,
    register,
  }
}

// 字段数组Hook
export function useFieldArray<T = any>(
  name: string,
  form: FormHookReturn<any>,
  defaultValue: T[] = []
) {
  const fields = (form.data[name] as T[]) || defaultValue

  const append = useCallback((value: T) => {
    const newFields = [...fields, value]
    form.setFieldValue(name, newFields)
  }, [fields, form.setFieldValue, name])

  const prepend = useCallback((value: T) => {
    const newFields = [value, ...fields]
    form.setFieldValue(name, newFields)
  }, [fields, form.setFieldValue, name])

  const remove = useCallback((index: number) => {
    const newFields = fields.filter((_, i) => i !== index)
    form.setFieldValue(name, newFields)
  }, [fields, form.setFieldValue, name])

  const insert = useCallback((index: number, value: T) => {
    const newFields = [...fields]
    newFields.splice(index, 0, value)
    form.setFieldValue(name, newFields)
  }, [fields, form.setFieldValue, name])

  const move = useCallback((from: number, to: number) => {
    const newFields = [...fields]
    const item = newFields.splice(from, 1)[0]
    newFields.splice(to, 0, item)
    form.setFieldValue(name, newFields)
  }, [fields, form.setFieldValue, name])

  const swap = useCallback((indexA: number, indexB: number) => {
    const newFields = [...fields]
    ;[newFields[indexA], newFields[indexB]] = [newFields[indexB], newFields[indexA]]
    form.setFieldValue(name, newFields)
  }, [fields, form.setFieldValue, name])

  const update = useCallback((index: number, value: T) => {
    const newFields = [...fields]
    newFields[index] = value
    form.setFieldValue(name, newFields)
  }, [fields, form.setFieldValue, name])

  const replace = useCallback((newFields: T[]) => {
    form.setFieldValue(name, newFields)
  }, [form.setFieldValue, name])

  return {
    fields,
    append,
    prepend,
    remove,
    insert,
    move,
    swap,
    update,
    replace,
  }
}

// 表单持久化Hook
export function useFormPersist<T extends FormData>(
  key: string,
  form: FormHookReturn<T>,
  options: {
    storage?: Storage
    debounceMs?: number
    exclude?: string[]
  } = {}
) {
  const { storage = localStorage, debounceMs = 500, exclude = [] } = options
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  // 保存到存储
  const saveToStorage = useCallback(() => {
    try {
      const dataToSave = { ...form.data }
      exclude.forEach(field => {
        delete dataToSave[field]
      })
      storage.setItem(key, JSON.stringify(dataToSave))
    } catch (error) {
      console.warn('Failed to save form data to storage:', error)
    }
  }, [form.data, key, storage, exclude])

  // 从存储加载
  const loadFromStorage = useCallback(() => {
    try {
      const saved = storage.getItem(key)
      if (saved) {
        const data = JSON.parse(saved)
        form.setValues(data)
        return true
      }
    } catch (error) {
      console.warn('Failed to load form data from storage:', error)
    }
    return false
  }, [key, storage, form.setValues])

  // 清除存储
  const clearStorage = useCallback(() => {
    try {
      storage.removeItem(key)
    } catch (error) {
      console.warn('Failed to clear form data from storage:', error)
    }
  }, [key, storage])

  // 防抖保存
  useEffect(() => {
    if (form.isDirty) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      
      timeoutRef.current = setTimeout(() => {
        saveToStorage()
      }, debounceMs)
    }
    
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [form.data, form.isDirty, saveToStorage, debounceMs])

  // 组件挂载时加载
  useEffect(() => {
    loadFromStorage()
  }, [])

  return {
    saveToStorage,
    loadFromStorage,
    clearStorage,
  }
}

// 导出验证器
export { validators }
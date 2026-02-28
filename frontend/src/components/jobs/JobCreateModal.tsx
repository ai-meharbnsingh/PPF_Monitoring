import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { jobsApi } from '@/api/jobs'
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch'
import { addJob } from '@/store/slices/jobsSlice'
import type { JobCreate } from '@/types/job'
import { WORK_TYPE_OPTIONS } from '@/types/common'
import toast from 'react-hot-toast'

interface JobCreateModalProps {
  isOpen: boolean
  onClose: () => void
  workshopId: number
}

interface FormValues {
  pit_id: string
  work_type: string
  car_model: string
  car_plate: string
  car_color: string
  customer_name: string
  customer_phone: string
  customer_email: string
  quoted_price: string
  estimated_duration_minutes: string
  owner_notes: string
}

export function JobCreateModal({ isOpen, onClose, workshopId }: JobCreateModalProps) {
  const dispatch = useAppDispatch()
  const pits = useAppSelector((s) => s.pits.pits)
  const [submitting, setSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>()

  const pitOptions = pits.map((p) => ({ value: String(p.id), label: p.name }))

  const onSubmit = async (data: FormValues) => {
    setSubmitting(true)
    try {
      const payload: JobCreate = {
        pit_id: Number(data.pit_id),
        work_type: data.work_type as JobCreate['work_type'],
        car_model: data.car_model || undefined,
        car_plate: data.car_plate || undefined,
        car_color: data.car_color || undefined,
        customer_name: data.customer_name || undefined,
        customer_phone: data.customer_phone || undefined,
        customer_email: data.customer_email || undefined,
        quoted_price: data.quoted_price ? Number(data.quoted_price) : undefined,
        estimated_duration_minutes: data.estimated_duration_minutes
          ? Number(data.estimated_duration_minutes)
          : undefined,
        owner_notes: data.owner_notes || undefined,
        currency: 'INR',
      }
      const created = await jobsApi.create(workshopId, payload)
      dispatch(
        addJob({
          id: created.id,
          workshop_id: created.workshop_id,
          pit_id: created.pit_id,
          pit_name: pits.find((p) => p.id === created.pit_id)?.name ?? null,
          car_model: created.car_model,
          car_plate: created.car_plate,
          work_type: created.work_type,
          status: created.status,
          quoted_price: created.quoted_price,
          currency: created.currency,
          scheduled_start_time: created.scheduled_start_time,
          actual_start_time: created.actual_start_time,
          estimated_end_time: created.estimated_end_time,
          actual_end_time: created.actual_end_time,
          created_at: created.created_at,
          customer_name: created.customer?.first_name ?? null,
          tracking_code: created.tracking_code ?? null,
        }),
      )
      toast.success('Job created!')
      reset()
      onClose()
    } catch {
      toast.error('Failed to create job')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create New Job" size="lg">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Select
            label="Pit / Bay *"
            placeholder="Select pit"
            options={pitOptions}
            {...register('pit_id', { required: 'Select a pit' })}
            error={errors.pit_id?.message}
          />
          <Select
            label="Work Type *"
            placeholder="Select type"
            options={WORK_TYPE_OPTIONS.map((w) => ({ value: w, label: w }))}
            {...register('work_type', { required: 'Select work type' })}
            error={errors.work_type?.message}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Car Model"
            placeholder="e.g. Honda City"
            {...register('car_model')}
          />
          <Input
            label="Car Plate"
            placeholder="e.g. MH12AB1234"
            {...register('car_plate')}
          />
        </div>

        <Input
          label="Car Color"
          placeholder="e.g. White"
          {...register('car_color')}
        />

        <div className="border-t border-gray-100 pt-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Customer Info (optional)
          </p>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Customer Name"
              placeholder="Full name"
              {...register('customer_name')}
            />
            <Input
              label="Phone"
              placeholder="+91 9876543210"
              {...register('customer_phone')}
            />
          </div>
          <Input
            label="Email"
            type="email"
            placeholder="customer@email.com"
            {...register('customer_email')}
            className="mt-4"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Quoted Price (INR)"
            type="number"
            placeholder="e.g. 45000"
            {...register('quoted_price')}
          />
          <Input
            label="Est. Duration (min)"
            type="number"
            placeholder="e.g. 360"
            {...register('estimated_duration_minutes')}
          />
        </div>

        <Input
          label="Notes"
          placeholder="Internal notes..."
          {...register('owner_notes')}
        />

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" isLoading={submitting}>
            Create Job
          </Button>
        </div>
      </form>
    </Modal>
  )
}

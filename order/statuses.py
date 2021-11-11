class OrderStatus:
    DRAFT = "draft"  # fully editable, not confirmed order created by staff users
    CREATED = "created"  # order created
    CONFIRMED = "confirmed"  # order is confirmed
    PACKING = "packing"  # order has been packed
    PACKED = "packed"  # order has been packed
    ONTHEWAY = "on the way"  # order moved to delivery
    REVISED = "revised"  # order moved to delivery
    DELIVERED = "delivered"  # permanently delivered order
    DELAYED = "delayed"  # temporaraily delayed order
    COMPLETED = "completed"  # permanently delivered order
    PICKED = "picked"  # permanently picked order
    CLOSED = "closed"  # permanently closed order
    CANCELLED = "cancelled"  # permanently canceled order
    CANCEL_REQUESTED = "cancel_requested"  # Request for order cancel
    CANCEL_APPROVED = "cancel_approved"  # Request for order cancel
    REFUNDED = "refund"  #
    REPLACED = "replacement"  #
    RETURNED = "return"  #
    PARTIAL_REFUND = "partial_refund"  #
    PARTIAL_REPLACE = "partial_replace"  #
    PARTIAL_RETURN = "partial_return"  #
    PARTIAL_REFUND_REPLACE = "partial_refund_replace"  #
    PARTIAL_RETURN_REPLACE = "partial_return_replace"  #
    PARTIAL_RETURN_REFUND = "partial_return_refund"  #
    RETURN_PICKED='return_picked'
    OPEN_PO = 'open_purchase_order'
    CLOSED_PO = 'close_purchase_order'

    CHOICES = [
        (DRAFT, "draft"),
        (CREATED, "created"),
        (CONFIRMED, "confirmed"),
        (COMPLETED, "completed"),
        (PACKING, "packing"),
        (PACKED, "packed"),
        (ONTHEWAY, "on the way"),
        (DELIVERED, "delivered"),
        (CLOSED, "closed"),
        (CANCELLED, "cancelled"),
        (OPEN_PO,"open_po"),
        (CLOSED_PO,"closed_po")
    ]

    SECONDARY_CHOICES = [
        (CREATED, "created"),
        (DELIVERED, "delivered"),
        (REVISED, "revised"),
        (PICKED, "picked"),
        (REFUNDED, "refund"),
        (DELAYED, "delayed"),
        (REPLACED, "replacement"),
        (RETURNED, "return"),
        (PARTIAL_REFUND, "partial_refund"),
        (PARTIAL_REPLACE, "partial_replace"),
        (PARTIAL_RETURN, "partial_return"),
        (PARTIAL_REFUND_REPLACE, "partial_refund_replace"),
        (PARTIAL_RETURN_REPLACE, "partial_return_replace"),
        (PARTIAL_RETURN_REFUND, "partial_return_refund"),
        (RETURN_PICKED, "return_picked"),
        (CANCEL_REQUESTED, "cancel_requested"),
        (CANCEL_APPROVED, "cancel_approved")

    ]


class OrderEvents:
    """The different order event types."""

    DRAFT_CREATED = "draft_created"
    DELIVERY_DATE_REVISED = "delivery_date_revised"
    CONFIRMED = "confirmed"  # order is confirmed
    PACKING = "packing"  # order has been packed
    PACKED = "packed"  # order has been packed
    ONTHEWAY = "on the way"  # order moved to delivery
    REVISED = "revised"  # order moved to delivery
    DELIVERED = "delivered"  # permanently delivered order
    DRAFT_ADDED_PRODUCTS = "draft_added_products"
    DRAFT_REMOVED_PRODUCTS = "draft_removed_products"

    PLACED = "placed"
    PLACED_FROM_DRAFT = "placed_from_draft"

    OVERSOLD_ITEMS = "oversold_items"
    CANCELED = "canceled"

    ORDER_MARKED_AS_PAID = "order_marked_as_paid"
    ORDER_FULLY_PAID = "order_fully_paid"

    UPDATED_ADDRESS = "updated_address"

    EMAIL_SENT = "email_sent"

    PAYMENT_AUTHORIZED = "payment_authorized"
    PAYMENT_CAPTURED = "payment_captured"
    PAYMENT_REFUNDED = "payment_refunded"
    PAYMENT_VOIDED = "payment_voided"
    PAYMENT_FAILED = "payment_failed"
    EXTERNAL_SERVICE_NOTIFICATION = "external_service_notification"

    INVOICE_REQUESTED = "invoice_requested"
    INVOICE_GENERATED = "invoice_generated"
    INVOICE_UPDATED = "invoice_updated"
    INVOICE_SENT = "invoice_sent"

    FULFILLMENT_CANCELED = "fulfillment_canceled"
    FULFILLMENT_RESTOCKED_ITEMS = "fulfillment_restocked_items"
    FULFILLMENT_FULFILLED_ITEMS = "fulfillment_fulfilled_items"
    TRACKING_UPDATED = "tracking_updated"
    NOTE_ADDED = "note_added"

    # Used mostly for importing legacy data from before Enum-based events
    OTHER = "other"

    # CHOICES = [
    #     (DRAFT_CREATED, "The draft order was created"),
    #     (DRAFT_ADDED_PRODUCTS, "Some products were added to the draft order"),
    #     (DRAFT_REMOVED_PRODUCTS, "Some products were removed from the draft order"),
    #     (PLACED, "The order was placed"),
    #     (PLACED_FROM_DRAFT, "The draft order was placed"),
    #     (OVERSOLD_ITEMS, "The draft order was placed with oversold items"),
    #     (CANCELED, "The order was canceled"),
    #     (ORDER_MARKED_AS_PAID, "The order was manually marked as fully paid"),
    #     (ORDER_FULLY_PAID, "The order was fully paid"),
    #     (UPDATED_ADDRESS, "The address from the placed order was updated"),
    #     (EMAIL_SENT, "The email was sent"),
    #     (PAYMENT_AUTHORIZED, "The payment was authorized"),
    #     (PAYMENT_CAPTURED, "The payment was captured"),
    #     (EXTERNAL_SERVICE_NOTIFICATION, "Notification from external service"),
    #     (PAYMENT_REFUNDED, "The payment was refunded"),
    #     (PAYMENT_VOIDED, "The payment was voided"),
    #     (PAYMENT_FAILED, "The payment was failed"),
    #     (INVOICE_REQUESTED, "An invoice was requested"),
    #     (INVOICE_GENERATED, "An invoice was generated"),
    #     (INVOICE_UPDATED, "An invoice was updated"),
    #     (INVOICE_SENT, "An invoice was sent"),
    #     (FULFILLMENT_CANCELED, "A fulfillment was canceled"),
    #     (FULFILLMENT_RESTOCKED_ITEMS, "The items of the fulfillment were restocked"),
    #     (FULFILLMENT_FULFILLED_ITEMS, "Some items were fulfilled"),
    #     (TRACKING_UPDATED, "The fulfillment's tracking code was updated"),
    #     (NOTE_ADDED, "A note was added to the order"),
    #     (OTHER, "An unknown order event containing a message"),
    # ]

    CHOICES = [
        (DRAFT_CREATED, DRAFT_CREATED),
        (DRAFT_ADDED_PRODUCTS,DRAFT_ADDED_PRODUCTS ),
        (DRAFT_REMOVED_PRODUCTS,DRAFT_REMOVED_PRODUCTS ),
        (PLACED, PLACED),
        (DELIVERY_DATE_REVISED, DELIVERY_DATE_REVISED),
        (PLACED_FROM_DRAFT, PLACED_FROM_DRAFT),
        (OVERSOLD_ITEMS, OVERSOLD_ITEMS),
        (CANCELED, CANCELED),
        (ORDER_MARKED_AS_PAID, ORDER_MARKED_AS_PAID),
        (ORDER_FULLY_PAID, ORDER_FULLY_PAID),
        (UPDATED_ADDRESS, UPDATED_ADDRESS),
        (EMAIL_SENT, EMAIL_SENT),
        (PAYMENT_AUTHORIZED, PAYMENT_AUTHORIZED),
        (PAYMENT_CAPTURED, PAYMENT_CAPTURED),
        (EXTERNAL_SERVICE_NOTIFICATION, EXTERNAL_SERVICE_NOTIFICATION),
        (PAYMENT_REFUNDED, PAYMENT_REFUNDED),
        (PAYMENT_VOIDED, PAYMENT_VOIDED),
        (PAYMENT_FAILED, PAYMENT_FAILED),
        (INVOICE_REQUESTED,INVOICE_REQUESTED ),
        (INVOICE_GENERATED, INVOICE_GENERATED),
        (INVOICE_UPDATED, INVOICE_UPDATED),
        (INVOICE_SENT, INVOICE_SENT),
        (FULFILLMENT_CANCELED, FULFILLMENT_CANCELED),
        (FULFILLMENT_RESTOCKED_ITEMS, FULFILLMENT_RESTOCKED_ITEMS),
        (FULFILLMENT_FULFILLED_ITEMS, FULFILLMENT_FULFILLED_ITEMS),
        (TRACKING_UPDATED, TRACKING_UPDATED),
        (NOTE_ADDED, NOTE_ADDED),
        (OTHER, OTHER),
    ]


class OrderEventsEmails:
    """The different order emails event types."""

    PAYMENT = "payment_confirmation"
    SHIPPING = "shipping_confirmation"
    TRACKING_UPDATED = "tracking_updated"
    ORDER_CONFIRMATION = "order_confirmation"
    ORDER_CANCEL = "order_cancel"
    ORDER_REFUND = "order_refund"
    FULFILLMENT = "fulfillment_confirmation"
    DIGITAL_LINKS = "digital_links"

    CHOICES = [
        (PAYMENT, "The payment confirmation email was sent"),
        (SHIPPING, "The shipping confirmation email was sent"),
        (TRACKING_UPDATED, "The fulfillment tracking code email was sent"),
        (ORDER_CONFIRMATION, "The order placement confirmation email was sent"),
        (ORDER_CANCEL, "The order cancel confirmation email was sent"),
        (ORDER_REFUND, "The order refund confirmation email was sent"),
        (FULFILLMENT, "The fulfillment confirmation email was sent"),
        (DIGITAL_LINKS, "The email containing the digital links was sent"),
    ]
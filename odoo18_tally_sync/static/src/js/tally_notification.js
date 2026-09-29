/** @odoo-module **/

import { registry } from "@web/core/registry";

const actionRegistry = registry.category("actions");
const originalDisplayNotification = actionRegistry.get("display_notification");

/**
 * Enhanced display_notification handler for Odoo 18.
 * Supports a custom `duration` (e.g., 5000ms for 5-second popup notifications)
 * for both success and failure messages without getting permanently stuck on screen.
 */
actionRegistry.add(
    "display_notification",
    async (env, action) => {
        const params = action.params || {};
        const duration = params.duration || (params.sticky === false ? 5000 : null);

        // When a custom duration is provided and notification is not permanently sticky
        if (duration && !params.sticky) {
            return new Promise((resolve) => {
                let isClosed = false;

                const closeNotification = async () => {
                    if (isClosed) {
                        return;
                    }
                    isClosed = true;

                    if (typeof closeFn === "function") {
                        closeFn();
                    }

                    if (params.next) {
                        await env.services.action.doAction(params.next);
                    }
                    resolve();
                };

                // Add notification with sticky: true so Odoo's internal 4s timer doesn't interfere;
                // our explicit duration timer manages closing after exactly `duration` ms.
                const closeFn = env.services.notification.add(params.message || "", {
                    title: params.title,
                    type: params.type || "info",
                    sticky: true,
                    className: params.className || "o_tally_notification",
                    buttons: params.links,
                    onClose: closeNotification,
                });

                // Auto-close after the specified duration (default: 5000ms = 5 seconds)
                setTimeout(() => {
                    closeNotification();
                }, duration);
            });
        }

        // Fallback to standard Odoo notification handler
        if (originalDisplayNotification) {
            return originalDisplayNotification(env, action);
        }
    },
    { force: true }
);

# ASTHRAL Unified UX research and applied decisions

Date: 2026-11-15. Product interface language: English.

## Research basis

- Nielsen Norman Group, [Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/): expose the common task first and keep advanced controls available on demand.
- Nielsen Norman Group, [4 Principles to Reduce Cognitive Load in UX Design](https://www.nngroup.com/articles/4-principles-reduce-cognitive-load/): organize information around the user's task and avoid making people remember details across screens.
- W3C, [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/): keyboard operation, visible focus, contrast, target sizing and accessible status feedback.
- web.dev, [Learn PWA](https://web.dev/learn/pwa/): keep the application shell independent from optional large resources and report offline capabilities honestly.
- OWASP, [Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html): do not imply remote identity assurance where none exists; provide clear authentication feedback.
- Android Developers, [Build responsive navigation](https://developer.android.com/develop/ui/views/layout/build-responsive-navigation): adapt primary navigation to compact and expanded layouts.

## Decisions applied

1. The initial local sign-in has exactly two fields (email and password). Account creation is a separate, initially hidden form. The synthetic demo entry is placed after the whole sign-in area.
2. The account's email is a device-local identifier, encrypted with the existing profile key. It is not submitted to a server, verified as an identity, or used for cloud recovery. Legacy profiles remain unlockable with their original passphrase and can add the identifier after unlock; the key is not rotated.
3. The workspace uses a compact desktop side rail and five primary mobile destinations. Secondary destinations are grouped under “More.” Only one task view is shown at a time; advanced traces and device diagnostics remain available in Settings/Developer View.
4. The Overview presents recent local records and explicit next actions. Assessment, monitoring, history, references, assistant, voice and vision have dedicated views. Critical urgency and protocol-safety restrictions remain visible within assessment results.
5. The assistant presents user questions, local evidence and generated explanations as separate message types. If no local model is loaded or verification rejects the output, the interface labels the response as verbatim evidence; it does not claim generation.
6. Voice transcripts can populate a chat question, but require the user to review and submit them. No recording starts automatically and raw audio is not persisted.
7. Vision image intake validates file type, size and dimensions in memory, revokes previews on tab hide, and clearly states when inference is not available. No images are sent to an external service or stored in offline caches.
8. The redesign uses semantic labels, live status regions, visible keyboard focus, reduced-motion handling, 44-pixel minimum actions and responsive navigation. Automated checks do not establish WCAG conformance; manual assistive-technology review remains necessary.

## Limits

This is a research prototype for synthetic data. UX and software checks do not validate clinical safety, operational suitability, assistive-technology conformance, local model quality, or physical-device behavior. Browser-local email identifiers are not globally unique and have no recovery channel. The static PWA currently has no compatible browser CV model assets; vision inference must remain unavailable until a properly licensed, compatible model/runtime is integrated and verified.

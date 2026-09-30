// Booking Mini App: services -> day -> time -> confirm, plus "my bookings".
// Talks to our API with the Telegram login string in the Authorization header.
(function () {
  "use strict";

  const tg = window.Telegram && window.Telegram.WebApp;
  const initData = tg ? tg.initData : "";
  const state = { services: [], service: null, day: null, slot: null, stack: [] };

  const $ = (id) => document.getElementById(id);
  const screens = ["services", "days", "slots", "confirm", "done", "my", "error"];

  function show(name, push = true) {
    const current = screens.find((s) => !$("screen-" + s).hidden);
    if (push && current && current !== name && !["done", "error"].includes(current)) state.stack.push(current);
    screens.forEach((s) => ($("screen-" + s).hidden = s !== name));
    const bookingTab = name !== "my";
    $("tab-book").setAttribute("aria-selected", String(bookingTab));
    $("tab-my").setAttribute("aria-selected", String(!bookingTab));
    if (tg) {
      state.stack.length && name !== "services" ? tg.BackButton.show() : tg.BackButton.hide();
      name === "confirm" ? tg.MainButton.show() : tg.MainButton.hide();
    }
    $("confirm-fallback").hidden = !(name === "confirm" && !tg);
  }

  function back() {
    const previous = state.stack.pop();
    show(previous || "services", false);
  }

  function toast(text) {
    const el = $("toast");
    el.textContent = text;
    el.hidden = false;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => (el.hidden = true), 3500);
  }

  function haptic(kind) {
    if (tg && tg.HapticFeedback) tg.HapticFeedback.notificationOccurred(kind);
  }

  async function api(path, options = {}) {
    const headers = { "Content-Type": "application/json" };
    if (initData) headers.Authorization = "tma " + initData;
    const response = await fetch(path, { ...options, headers });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(body.detail || "Ошибка " + response.status);
      error.status = response.status;
      throw error;
    }
    return body;
  }

  function button(className, html, onClick) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = className;
    b.innerHTML = html;
    b.addEventListener("click", onClick);
    return b;
  }

  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

  function renderServices() {
    const list = $("services");
    list.replaceChildren();
    state.services.forEach((service) => {
      const li = document.createElement("li");
      li.append(button("item", `<span>${esc(service.title)}</span><span class="price">${esc(service.price || "")}</span>`, () => pickService(service)));
      list.append(li);
    });
  }

  async function pickService(service) {
    state.service = service;
    $("days-service").textContent = service.title;
    const days = await api("/api/days?service_id=" + encodeURIComponent(service.id));
    const box = $("days");
    box.replaceChildren();
    days.forEach((day) => {
      const b = button("chip", `<span>${esc(day.label)}</span><small>${day.free ? "свободно " + day.free : "нет мест"}</small>`, () => pickDay(day));
      b.disabled = day.free === 0;
      box.append(b);
    });
    show("days");
  }

  async function pickDay(day, push = true) {
    state.day = day;
    const data = await api(`/api/slots?service_id=${encodeURIComponent(state.service.id)}&day=${day.date}`);
    $("slots-title").textContent = `${state.service.title}, ${data.label}`;
    const grid = $("slots");
    grid.replaceChildren();
    data.slots.forEach((slot) => grid.append(button("slot", esc(slot.time), () => pickSlot(slot))));
    $("slots-empty").hidden = data.slots.length > 0;
    show("slots", push);
  }

  function pickSlot(slot) {
    state.slot = slot;
    $("confirm-service").textContent = state.service.title;
    $("confirm-when").textContent = `${state.day.label}, ${slot.time}`;
    $("confirm-price").textContent = state.service.price ? "Стоимость: " + state.service.price : "";
    if (tg) tg.MainButton.setText("Записаться на " + slot.time);
    show("confirm");
  }

  async function confirm() {
    if (tg) tg.MainButton.showProgress();
    try {
      const booking = await api("/api/bookings", {
        method: "POST",
        body: JSON.stringify({ service_id: state.service.id, ts: state.slot.ts }),
      });
      haptic("success");
      $("done-text").textContent = `${booking.service}, ${booking.when}`;
      state.stack = [];
      show("done", false);
    } catch (error) {
      haptic("error");
      toast(error.message);
      if (error.status === 409) await pickDay(state.day, false); // someone was faster: fresh times
    } finally {
      if (tg) tg.MainButton.hideProgress();
    }
  }

  async function openMy() {
    state.stack = [];
    const bookings = await api("/api/bookings");
    const list = $("my");
    list.replaceChildren();
    bookings.forEach((b) => {
      const li = document.createElement("li");
      li.className = "item";
      li.innerHTML = `<span><b>${esc(b.service)}</b><br><span class="price">${esc(b.when)}</span></span>`;
      li.append(button("danger", "Отменить", () => cancel(b)));
      list.append(li);
    });
    $("my-empty").hidden = bookings.length > 0;
    show("my", false);
  }

  async function cancel(booking) {
    const ask = `Отменить запись: ${booking.service}, ${booking.when}?`;
    const ok = await new Promise((resolve) => (tg ? tg.showConfirm(ask, resolve) : resolve(true)));
    if (!ok) return;
    try {
      await api("/api/bookings/" + booking.id, { method: "DELETE" });
      haptic("success");
      toast("Запись отменена");
    } catch (error) {
      toast(error.message);
    }
    await openMy();
  }

  function guard(fn) {
    return (...args) => fn(...args).catch((error) => toast(error.message));
  }

  async function start() {
    if (tg) {
      tg.ready();
      tg.expand();
      tg.BackButton.onClick(back);
      tg.MainButton.onClick(guard(confirm));
    }
    $("confirm-fallback").addEventListener("click", guard(confirm));
    $("done-again").addEventListener("click", () => { state.stack = []; show("services", false); });
    $("tab-book").addEventListener("click", () => { state.stack = []; show("services", false); });
    $("tab-my").addEventListener("click", guard(openMy));
    try {
      const config = await api("/api/config");
      $("shop").textContent = config.shop;
      document.title = config.shop;
      state.services = config.services;
      renderServices();
      show("services", false);
    } catch (error) {
      if (error.status !== 401) $("error-text").textContent = error.message;
      show("error", false);
    }
  }

  start();
})();

$(document).ready(function() {
    // Инициализация календаря
    $('#calendar').fullCalendar({
        header: {
            left: 'prev,next today',
            center: 'title',
            right: 'month,agendaWeek,agendaDay'
        },
        events: function(start, end, timezone, callback) {
            $.ajax({
                url: '/get_events', // Допустим, мы загружаем события через этот маршрут
                dataType: 'json',
                success: function(data) {
                    var events = data.map(function(event) {
                        return {
                            title: event.event_name,
                            start: event.event_date,
                            description: event.description,
                            location: event.location,
                            id: event.idevents
                        };
                    });
                    callback(events);
                }
            });
        },

        // Обработка клика на событие календаря
        eventClick: function(calEvent, jsEvent, view) {
            // Открыть модальное окно с деталями события
            openEditEventModal(calEvent);
        }
    });

    // Обработка редактирования события через AJAX
    $('form#edit_event_form').submit(function(e) {
        e.preventDefault();

        var formData = $(this).serialize(); // Собираем данные из формы
        var eventId = $('#edit_event_id').val(); // Получаем ID события

        $.ajax({
            type: 'POST',
            url: '/edit_event/' + eventId,
            data: formData,
            success: function(response) {
                alert('Событие обновлено успешно');
                $('#calendar').fullCalendar('refetchEvents'); // Перезагружаем календарь
                $('#editEventModal').modal('hide'); // Закрываем модальное окно
            },
            error: function(xhr, status, error) {
                alert('Ошибка при обновлении события: ' + error);
            }
        });
    });

    // Открытие модального окна для редактирования события
    function openEditEventModal(calEvent) {
        $('#edit_event_id').val(calEvent.id);
        $('#edit_event_name').val(calEvent.title);
        $('#edit_event_date').val(calEvent.start.format('YYYY-MM-DD'));
        $('#edit_event_description').val(calEvent.description);
        $('#edit_event_location').val(calEvent.location);

        // Открываем модальное окно
        $('#editEventModal').modal('show');
    }

    // Удаление события через AJAX
    $('button.delete_event').click(function(e) {
        e.preventDefault();

        var eventId = $(this).data('event-id');
        $.ajax({
            type: 'POST',
            url: '/delete_event/' + eventId,
            success: function(response) {
                alert('Событие удалено успешно');
                $('#calendar').fullCalendar('refetchEvents'); // Обновляем календарь
            },
            error: function(xhr, status, error) {
                alert('Ошибка при удалении события: ' + error);
            }
        });
    });

    // Удаление встречи через AJAX
    $('button.delete_meeting').click(function(e) {
        e.preventDefault();

        var meetingId = $(this).data('meeting-id');
        $.ajax({
            type: 'POST',
            url: '/delete_meeting/' + meetingId,
            success: function(response) {
                alert('Встреча удалена успешно');
                $('#calendar').fullCalendar('refetchEvents'); // Обновляем календарь
            },
            error: function(xhr, status, error) {
                alert('Ошибка при удалении встречи: ' + error);
            }
        });
    });
});

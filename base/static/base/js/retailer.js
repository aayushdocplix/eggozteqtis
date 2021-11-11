$("#id_city").change(function () {
  var url = $("#retailForm").attr("data-clusters-url");  // get the url of the `load_cities` view
  var cityId = $(this).val();  // get the selected city ID from the HTML input
    if (cityId > 0){
        $.ajax({                       // initialize an AJAX request
            url: url,                    // set the url of the request (= localhost:8000/hr/ajax/load-classes/)
            data: {
              'city': cityId       // add the cityid to the GET parameters
            },
            success: function (data) {
               console.log(data);// `data` is the return of the `load_classes` view function
              $("#id_cluster").html(data);  // replace the contents of the city input with the data that came from the server
            }
          });
    }else{
        $("#id_cluster").html('<option value="0">-------</option>');
    }
});


$("#id_city").change(function () {
  var url = $("#retailForm").attr("data-sales_persons-url");  // get the url of the `load_cities` view
  var cityId = $(this).val();  // get the selected city ID from the HTML input
    if (cityId > 0){
        $.ajax({                       // initialize an AJAX request
            url: url,                    // set the url of the request (= localhost:8000/hr/ajax/load-classes/)
            data: {
              'city': cityId       // add the cityid to the GET parameters
            },
            success: function (data) {
               console.log(data);// `data` is the return of the `load_classes` view function
              $("#id_sales_person").html(data);  // replace the contents of the city input with the data that came from the server
            }
          });
    }else{
        $("#id_sales_person").html('<option value="0">-------</option>');
    }
});
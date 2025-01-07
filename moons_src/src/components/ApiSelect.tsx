import AsyncSelect from "react-select/async";

const colourStyles = {
  option: (styles: any) => {
    return {
      ...styles,
      color: "black",
    };
  },
};

export const ApiSelect = ({ setValue, apiLookup }: any) => {
  function handleChange(newValue: any) {
    console.log("Selected: " + newValue.label);
    setValue(newValue);
  }

  return (
    <AsyncSelect
      cacheOptions
      styles={colourStyles}
      loadOptions={apiLookup}
      defaultOptions={[]}
      onChange={handleChange}
    />
  );
};
